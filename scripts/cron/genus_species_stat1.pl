#!/usr/bin/perl
#use 5.010;
#----------------
#  This script updates num species, hybrids, and image counts in Genus table
#------
##############################
use warnings FATAL => 'all';
use strict;
use Dotenv;
use DBI;
use Time::Duration;
use POSIX qw(strftime);
use Cwd qw(abs_path);
use File::Basename qw(dirname);

# Determine the current environment
my $env = determine_environment();

# Load the appropriate .env file
Dotenv->load("/webapps/$env/.env");

my $HOST = '134.209.46.210';
my $DB = $ENV{'DBNAME'};

my $dbh = DBI->connect( "DBI:MariaDB:$DB:$ENV{'DBHOST'}","chariya",$ENV{'MYDBPSSWD'}) or die( "Could not connect to: $DBI::errstr" );
my ($sth, $sth1);
&getASPM("use $DB");
# use open qw(:locale);

my @apps = (
	'orchidaceae',
	# 'other',
	# 'fungi',
	# 'aves',
	# 'animalia'
);
my $date = strftime "%Y-%m-%d:%H:%M-%S", localtime;
# our ($DB,$stf,$sth, $rc, $sth1, $sth2, $dbh);
# my $datestring = strftime "%a %b %e %H:%M:%S %Y", localtime();
my $datetime = localtime();
my $start_time = time();
my $debug = 1;
my ($stmt, %pid, %gen, %num_image,%num_species, %num_hybrid, %num_hybimage, %num_spcimage,
	%num_hyb_with_image,%num_spc_with_image,@accepted, %synonym,
	%num_species_synonym,%num_hybrid_synonym,%num_synonym, %genus,
	%num_species_total, %num_hybrid_total,%num_image_gen,
	%num_famhybimage, %num_famspcimage,
	%num_ancestor, %num_species_ancestor, %num_descendant, %num_dir_descendant
 );


foreach my $app (@apps) {
	print "\n$app\n";

	print "$app - Initialize PID\n" if $debug;
	getPID($app);

	print "$app - Count hybimages and spcimages\n" if $debug;
	getSpcImages($app);

	getHybImages($app) if $app eq 'orchidaceae';

	print "$app - get synonym pid\n" if $debug;
	getSynonymPid($app);

	print "$app - Processing genus\n" if $debug;
	procGenus($app);

	print "$app - Processing species\n" if $debug;
	getancdesc($app);
	procSpecies($app);

}

print "$date\t Runtime = ", duration(time() - $start_time), "\n";


sub procGenus {
	my $app = shift;
	my $i = 0;
	# &getASPM("UPDATE bluenanta_genus set num_species = 0, num_hybrid = 0, num_species_synonym=0, num_species_total=0,
	# 			num_spc_with_image=0,pct_spc_with_image=0,num_hybrid=0,num_hybrid_synonym=0,num_hybrid_total=0,
	# 			num_hyb_with_image=0,pct_hyb_with_image=0");

    # First, set all statistic fields to empty
	# Prepare stat values
	&getASPM("delete from orchidaceae_genusstat;");
	# foreach (sort keys %gen){print"$_\t$gen{$_}\n";}

	foreach my $pid (sort keys %gen) {
		# $num_species{$pid} = 0 if not $num_species {$pid};
		# $num_species_synonym{$pid} = 0 if not $num_species_synonym{$pid};
		$num_spcimage{$pid} = 0 if not $num_spcimage{$pid};
		# $num_species_total{$pid} = 0 if not $num_species_total{$pid};
		$num_spc_with_image{$pid} = 0 if not $num_spc_with_image{$pid};
		# $num_hybrid {$pid}= 0 if not $num_hybrid {$pid};
		# $num_hybrid_synonym{$pid} = 0 if not $num_hybrid_synonym{$pid} ;
		$num_hybimage{$pid} = 0 if not $num_hybimage{$pid};
		# $num_hybrid_total{$pid} = 0 if not $num_hybrid_total{$pid};
		$num_hyb_with_image{$pid} = 0 if not $num_hyb_with_image{$pid};



        $stmt = "insert into " . $app . "_genusstat (pid, num_species, num_species_synonym, num_spcimage,
        		num_species_total, num_spc_with_image, pct_spc_with_image,num_hybrid, num_hybrid_synonym,
        		num_hybimage, num_hybrid_total, num_hyb_with_image, pct_hyb_with_image, num_synonym) values (";
		$stmt .= "$pid, $num_species{$pid}, $num_species_synonym{$pid}, $num_spcimage{$pid}, ";

		my $total = $num_species{$pid} + $num_species_synonym{$pid};
		$stmt .= "$total, ";
		my $pct = 0;
		if ($num_spc_with_image{$pid}) {
			$pct = sprintf("%.1f", $num_spc_with_image{$pid} * 100 / $num_species{$pid}) if $num_species{$pid} > 0;
		}
		$stmt .= "$num_spc_with_image{$pid}, $pct, $num_hybrid{$pid}, $num_hybrid_synonym{$pid}, $num_hybimage{$pid}, ";
		$total = $num_hybrid{$pid} + $num_hybrid_total{$pid};
		$stmt .= "$total, ";
		$pct = 0;
        if ($num_hyb_with_image{$pid}) {
            $pct = sprintf("%.1f", $num_hyb_with_image{$pid} * 100 /$num_hybrid{$pid}) if $num_hybrid{$pid};
        }
        $stmt .= "$num_hyb_with_image{$pid}, $pct, $num_synonym{$pid} );";
		&getASPM($stmt);
	}
}


sub procSpecies {
	my $app = shift;
	my $i = 0;
	&getASPM("delete from orchidaceae_speciesstat;");
	foreach my $pid (sort keys %pid) {
		$num_image{$pid} = 0 if not $num_image{$pid};
		$num_ancestor{$pid} = 0 if not $num_ancestor{$pid};
		$num_species_ancestor{$pid} = 0 if not $num_species_ancestor{$pid};
		$num_descendant{$pid} = 0 if not $num_descendant{$pid};
		$num_dir_descendant{$pid} = 0 if not $num_dir_descendant{$pid};
        $stmt = "insert into orchidaceae_speciesstat
				(pid, num_image, num_ancestor, num_species_ancestor, num_descendant, num_dir_descendant)
				values ($pid, $num_image{$pid}, $num_ancestor{$pid}, $num_species_ancestor{$pid}, $num_descendant{$pid}, $num_dir_descendant{$pid});";
		&getASPM($stmt);
		# print "$i\t$stmt\n" if $debug and $i++%100==0; #$num_spcimage{$pid};
	}
}


# sub processSynonym {
# 	# Set num image for each synonym = num inage of its accepted species
# 	my $app = shift;
# 	my $i = 0;
#
# 	foreach (sort keys %synonym) {
# 		$stmt = "update " . $app . "_species set num_image = $synonym{$_} where pid = $_;";
# 		print "pid = $_\n $stmt\n" if $_ == 300000910282;
# 		&getASPM($stmt);
# 	}
# }



sub getPID {
	my $app = shift;
	$stmt = "select pid, type, gen, status from " . $app . "_species where pid > 0 and type is not null and gen is not null order by 3;";
	print "$stmt\n" if $debug;
	&getASPM($stmt);
	my $prevgen = 0;
    my %seen;
	while (my @row = $sth->fetchrow_array()) {
		$gen{$row[2]}++;
		$pid{$row[0]}++;
        if ($row[2] != $prevgen) {
			# Initialize all counts
            $genus{$row[2]} = 0;
			$num_species{$row[2]} = 0;
			$num_species_synonym{$row[2]} = 0;
			$num_hybrid{$row[2]} = 0;
			$num_hybrid_synonym{$row[2]} = 0;
			$num_image_gen{$row[2]} = 0;
		}
        $num_image{$row[0]} = 0;
		$genus{$row[2]}++;
		if ($row[1] eq 'species') {
			if ($row[3] eq 'synonym') {
				$num_species_synonym{$row[2]}++;
			}
			else {
				$num_species{$row[2]}++;
			}
		}
		elsif ($row[1] eq 'hybrid') {
			if ($row[3] eq 'synonym') {
				$num_hybrid_synonym{$row[2]}++;
			}
			else {
				$num_hybrid{$row[2]}++;
			}
		}
        else {
            print "What type is this: pid $row[0]\ttype: $row[1]\tgen: $row[2]\n";
        }
		$prevgen = $row[2];
	}

	foreach (sort keys %genus) {
		$num_species{$_} = 0 if not $num_species{$_};
		$num_species_synonym{$_} = 0 if not $num_species_synonym{$_};
		$num_hybrid{$_} = 0 if not $num_hybrid{$_};
		$num_hybrid_synonym{$_} = 0 if not $num_hybrid_synonym{$_};
		$num_synonym{$_} = $genus{$_} - $num_species{$_} - $num_hybrid{$_};
		$num_species_total{$_} = $num_species{$_} + $num_species_synonym{$_};
		$num_hybrid_total{$_} = $num_hybrid{$_} + $num_hybrid_synonym{$_};
	}

}


sub getSynonymPid {
	# Set num image for synonym to be the same as its accepted species
	my $app = shift;
	foreach (keys %num_image) {
		$stmt = "select spid, acc_id from " . $app . "_synonym where acc_id = $_ ";
		&getASPM($stmt);
		while (my @row = $sth->fetchrow_array()) {
			# next if $num_image{$_} == 0;
			$synonym{$row[0]} = $num_image{$row[0]};
		}
	}
}


sub getHybImages {
	my $app = shift;
	# Initialize num images
	$stmt = "select count(*) c, pid, gen from " . $app . "_hybimages where `rank` > 0 and pid < 999999999 group by 2, 3 order by 3;";
	&getASPM($stmt);
	my $prevgen = 0;
	while (my @row = $sth->fetchrow_array()) {
		if ($row[2] != $prevgen) {
			$num_image_gen{$row[2]} = 0;
			$num_hyb_with_image{$row[2]} = 0;
			$num_hybimage{$row[2]} = 0;
			$prevgen = $row[2];
		}
		next if $row[0] == 0;
		$num_image{$row[1]} = $row[0] if $row[1] and $row[0];
		# Data for genus stat
		$num_image_gen{$row[2]} += $row[0];
		$num_hyb_with_image{$row[2]}++;
		$num_hybimage{$row[2]} += $row[0];
	}
}


sub getSpcImages {
	my $app = shift;
	$stmt = "select count(*) c, pid, gen from " . $app . "_spcimages where `rank` > 0 group by 2, 3 order by 3;";
	print "$stmt\n" if $debug;
	&getASPM($stmt);
	my $prevgen = 0;
	while (my @row = $sth->fetchrow_array()) {
		next if not $row[1];
		if ($row[2] != $prevgen and $prevgen != 0) {
			$num_image_gen{$row[2]} = 0;
			$num_spc_with_image{$row[2]} = 0;
			$num_spcimage{$row[2]} = 0;
			$prevgen = $row[2];
		}
		next if $row[0] == 0;
		$num_image{$row[1]} = $row[0];
		$num_image_gen{$row[2]} += $row[0];
		$num_spc_with_image{$row[2]}++;
		$num_spcimage{$row[2]} += $row[0];
	}
}


sub getancdesc {
	$stmt = "select count(*), aid from orchidaceae_ancestordescendant group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
			$num_descendant{$row[1]} = $row[0];
			print "1 $row[1], $row[0]\n" if $row[1] == 1;
		}
	}

	$stmt = "select count(*), did from orchidaceae_ancestordescendant group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
			$num_ancestor{$row[1]} = $row[0];
			print "2 $row[1], $row[0]\n" if $row[1] == 1;
		}
	}

	$stmt = "select count(*), did from orchidaceae_ancestordescendant where anctype = 'species' group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
			$num_species_ancestor{$row[1]} = $row[0];
			print "3 $row[1], $row[0]\n" if $row[1] == 1;
		}
	}

	$stmt = "select count(*), seed_id from orchidaceae_hybrid group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
			$num_dir_descendant{$row[1]} = $row[0];
			print "4 $row[1], $row[0]\n" if $row[1] == 1;
		}
	}

	$stmt = "select count(*), pollen_id from orchidaceae_hybrid group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
			$num_dir_descendant{$row[1]} += $row[0];
		}
	}
}

sub getASPM {
	my $stmt = shift;
	$sth = $dbh->prepare( $stmt ) or die( "\n$stmt\nCannot prepare: ", $dbh->errstr(), "\n" );
	my $rc = $sth->execute() or die("\nDead! \n$stmt\nCannot execute: ", $sth->errstr(),"\n" );
}


# Function to determine the current environment
sub determine_environment {
    my $script_path = abs_path($0);
    my $script_dir = dirname($script_path);

    if ($script_dir =~ /bluenanta_dev/) {
        return 'bluenanta_dev';
    } elsif ($script_dir =~ /bluenanta/) {
        return 'bluenanta';
    } else {
        die "Unable to determine environment. Script is not in a recognized directory.";
    }
}

