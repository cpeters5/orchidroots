#!/usr/bin/perl
#use 5.010;
# #------
# This script extract species data from Kew.
# - Run with 1 parameter (family) and Empty species/genus tables = Build from scratch:
# - Run with 1 parameter (family) and Non empty species tables = Update tables:
# - Run with 1 parameter (family) and a list of genera = update (or build) just the passing genera
# - Run with 2 parameter (family, genus) = update (or build) species for the pasing genus
#  Steps:
# Get input file containing list of species from WCSP.
#
# 0)  Get page source of WCSP list
# 1)  Clear bromel table (genus, species, synonym, distribution, gensyn, accepted, hybrid)
#     Remove pid and gen foreign keys in all of these tables
# 2)  Delete all data/results/(distcode, species, missed, synonym)_refresh_20201210.dat
# 3)  Set $action parameter to 1 (run from scratch) or 0 (refresh existing bromel data)
# 4)  run getbromelfromkew.pl <family> [<genus>].  This will dump list in data/input directory.
#     Note: Get largest genera first upload to natural_genus and natural_species before the next run.
# 5)  Check missed record files, and add logic to process the missing records.
# 6)  When no more mised records, Load genus, species, distribution, synonym and gensyn.
# 7)  Recreated all pid and gen foreign keys
# 8)  Clear all output files except the two synonyms
# 9) Rerun with new genus parameters and repeat 2-7 untill all records for teh family are processed.
# 10)  Load accepted and hybrid table. manually create seed and pollen in hybrid table

#------
##############################
use warnings FATAL => 'all';
use strict;
use DBI;
use Time::Duration;
use POSIX qw(strftime);
use LWP::UserAgent;
use LWP::Protocol::https;
use LWP::Simple;
use WWW::Mechanize;



# my $HOST = '134.209.46.210'; #prod
my $HOST = '134.209.93.40'; #dev
my $DB = "orchiddev";
my $dbh = DBI->connect( "DBI:mysql:$DB:$HOST","chariya","Imh#r3r3") or die( "Could not connect to: $DBI::errstr" );
# my $dbh = DBI->connect( "DBI:ODBC:$DB") or die( "Could not connect to: $DBI::errstr" );		#local
my ($sth, $sth1);
&getASPM("use $DB");
my $datetime = localtime();
my $start_time = time();
my $debug = 1;
my $date = strftime "%Y-%m-%d:%H:%M-%S", localtime;

my $family  = lc($ARGV[0]);
my %genus;
my %GENUS;

getGenus($family);
extractGenus();

open OUT, ">:utf8","data/results/hybrid_" . $family . ".dat" or die "Cant open file: $!\n";
print OUT "pid\tpid1\tpid2\tgenus\thybrid\tauthor\tyear\tseed\tpollen\n";

my $i = 0;
foreach (sort keys %GENUS) {
    my $GENUS = $_;
    extractHybrid($GENUS);
    # last if $GENUS eq 'BROMELIA';
}


sub extractHybrid {
    my $GENUS = shift;
    my $mech = WWW::Mechanize->new(quiet=>1);
    my $ua = LWP::UserAgent->new;
    $ua->protocols_allowed(['https']);
    $mech->add_handler("request_send", sub { shift->dump; return });
    $mech->add_handler("response_done", sub { shift->dump; return });
    my $url  = "https://registry.bsi.org/index.php?genus=" . up $GENUS;
    $mech->get( $url );
    my $Con = $mech->content;
    my @lines = split(/\n/,$Con);
    my ($pid, $hybrid, $year, $seed, $pollen, $author) = ('','','','','','');
    foreach (@lines) {
        my $headurl = 'https://registry.bsi.org/index.php';
        next if $_ !~ /\?genus=.*id=([\d#]+)\'/;
        $pid = $1;
        next if $_ !~ /(\?[^\']+)\'/;
        my $detailurl = $headurl.$1;
        $detailurl =~ s/amp;//;
        my $mech2 = WWW::Mechanize->new(quiet=>1);
        my $ua2 = LWP::UserAgent->new;
        $ua2->protocols_allowed(['https']);
        $mech2->add_handler("request_send", sub { shift->dump; return });
        $mech2->add_handler("response_done", sub { shift->dump; return });
        $mech2->get( $detailurl );
        my $Con2 = $mech2->content;
        my @detail = split(/\n/,$Con2);

        for my $i (30 .. $#detail ) {
            next if $detail[$i] !~/<h1>Bromeliad Cultivar Register/;
            if ($detail[$i+3] =~ /;(.*)&/) {
                $hybrid = $1;
            }
            if($detail[$i+4] =~ /<b>(.*)<\/b>/){
                $author = $1;
            }
            if($detail[$i+5] =~ /<b>(.*)<\/b>/){
                $year = $1;
                print "$detail[$i+5]\n";
            }
            if($detail[$i+9] =~ /<b>(.*)<\/b>/){
                $seed = $1;
            }
            if($detail[$i+10] =~ /<b>(.*)<\/b>/) {
                 $pollen = $1;
            }
            my ($pid1,$pid2) = split(/#/,$pid);
            my $output = "$pid\t$pid1\t$pid2\t$GENUS\t$hybrid\t$author\t$year\t$seed\t$pollen\n";
            $output =~ s/\"/'/g;
            print  $i++ . " OUTPUT = $pid\t$pid1\t$pid2\t$GENUS\t$hybrid\t$author\t$year\t$seed\t$pollen\n";
            print OUT "$output\n";
        }
    }
}


sub extractGenus {
    open MISS, ">:utf8","data/results/missing-genus.dat" or die "Cant open file: $!\n";
    print MISS "Genus\n";
    my $GENUS;
    my $mech = WWW::Mechanize->new(quiet=>1);
    my $ua = LWP::UserAgent->new;
    $ua->protocols_allowed(['https']);
    $mech->add_handler("request_send", sub { shift->dump; return });
    $mech->add_handler("response_done", sub { shift->dump; return });
    my $url  = "https://registry.bsi.org/index.php" ;
    $mech->get( $url );
    my $Con = $mech->content;
    my @lines = split(/\n/,$Con);
    foreach (@lines) {
        next if $_ !~ /<li><a/;
        $_ =~ /genus=([A-Zx]+)\'/;
        print ">>> $1\t";
        my $a = substr($1,0,1) . lc($1);
        print ">>> $a\n";
        $GENUS{$a}++;
        my $gen = $1;
        $gen =~ s/^x//;
        # print "Missing $gen\n" if not $genus{lc $gen};
        print MISS "$gen\n" if not $genus{lc $gen};

    }
}


sub getGenus {
    my $family = shift;
    my $stmt = "select genus from " . $family . "_genus where family = '$family';";
    &getASPM($stmt);
    while (my @row = $sth->fetchrow_array()) {
        $genus{lc $row[0]}++;
    }
}


sub getASPM {
	my $stmt = shift;
	$sth = $dbh->prepare( $stmt ) or die( "\n$stmt\nCannot prepare: ", $dbh->errstr(), "\n" );
	my $rc = $sth->execute() or die("\nDead! \n$stmt\nCannot execute: ", $sth->errstr(),"\n" );
}
