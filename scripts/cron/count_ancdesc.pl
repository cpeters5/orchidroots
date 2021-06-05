#!/usr/bin/perl
#use 5.010;
#----------------
#  This script updates num species, hybrids, and image counts in Genus table
#------
##############################
use strict;
use warnings FATAL => 'all';
use DBI;
use Time::Duration;
use POSIX qw(strftime);

my $HOST = '134.209.46.210';
my $DB = "bluenanta";
my $dbh = DBI->connect( "DBI:mysql:$DB:$HOST","chariya","Imh#r3r3") or die( "Could not connect to: $DBI::errstr" );
my ($sth, $sth1);
&getASPM("use $DB");

# use open qw(:locale);

my $date = strftime "%Y-%m-%d:%H:%M-%S", localtime;
# our ($DB,$stf,$sth, $rc, $sth1, $sth2, $dbh);
# my $datestring = strftime "%a %b %e %H:%M:%S %Y", localtime();
my $datetime = localtime();
my $start_time = time();

my ($stmt,%pid, %num_ancestor, %num_species_ancestor, %num_descendant, %num_dir_descendant );

# print "Count hybimages and spcimages\n";
getancdesc();

# print "Processing species\n";
procSpecies();

print "$date\t Runtime = ", duration(time() - $start_time),"\n";

sub procSpecies {
	# print "\tUpdating num_ancestor for species\n";
	&getASPM("UPDATE orchidaceae_species set num_ancestor = 0, num_species_ancestor = 0, num_descendant=0");
	foreach my $pid (sort keys %pid) {
		$stmt = "update orchidaceae_species set ";
        if ($num_ancestor{$pid}) {
            $stmt .= "num_ancestor = $num_ancestor{$pid}, ";
        }
        if ($num_species_ancestor{$pid}) {
            $stmt .= "num_species_ancestor = $num_species_ancestor{$pid}, ";
        }
        if ($num_descendant{$pid}) {
            $stmt .= " num_descendant = $num_descendant{$pid}, ";
        }
        if ($num_dir_descendant{$pid}) {
            $stmt .= " num_dir_descendant = $num_dir_descendant{$pid}";
        }

        $stmt =~ s/, $//;
        $stmt .= " where pid = $pid";
		&getASPM($stmt);
	}

}


sub getancdesc {
	&getASPM("use $DB");

	$stmt = "select count(*), aid from orchidaceae_ancestordescendant group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
            $pid{$row[1]}++;
			$num_descendant{$row[1]} = $row[0];
		}
	}

	$stmt = "select count(*), did from orchidaceae_ancestordescendant group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
            $pid{$row[1]}++;
			$num_ancestor{$row[1]} = $row[0];
		}
	}

	$stmt = "select count(*), did from orchidaceae_ancestordescendant where anctype = 'species' group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
            $pid{$row[1]}++;
			$num_species_ancestor{$row[1]} = $row[0];
		}
	}

	$stmt = "select count(*), seed_id from orchidaceae_hybrid group by 2 order by 2;";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		if ($row[1]) {
            $pid{$row[1]}++;
			$num_dir_descendant{$row[1]} = $row[0];
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
