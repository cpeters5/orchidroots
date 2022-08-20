#!/usr/bin/perl
#-- Initial implementation 20171212
#-- Author: Chariya Punyanitya
#-----------------------------
#  get ip statistics by hour

use strict;
use warnings qw(all);
use Encode qw(encode decode);
use utf8;
use open qw(:locale);
use Time::Piece;

use DBI;
my $HOST = '134.209.46.210';   # orchiddb
my $DB = "bluenanta";
my $dbh = DBI->connect( "DBI:mysql:$DB:$HOST","chariya","Imh#r3r3") or die( "Could not connect to: $DBI::errstr" );
my ($sth, $sth1);
&getASPM("use $DB");


#require "common.pl";
#our ($sth);
my %ip = ();
my $debug = 1;
my $file = "/var/log/gunicorn/gunicorn-access.log";
my $grouping = 'day';
my $ip = '';
my $datetime = '';
my %dt;
my $app = $ARGV[0];
my $format = '%Y-%m-%d';
my %mon2num = qw(
    Jan 1  Feb 2  Mar 3  Apr 4  May 5  Jun 6
    Jul 7  Aug 8  Sep 9  Oct 10 Nov 11 Dec 12
);
my %mon2str = qw(
    1 Jan 2  Feb 3  Mar 4  Apr 5  May 6  Jun
    7 Jul 8  Aug 9  Sep 10  Oct 11 Nov 12 Dec
);
my %maxhit = qw(
    orchidlist 300 detail 2000 search 20
);

my $tab = "logstat_byday";
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime();
$mon++;
$mon = sprintf("%02d", $mon);
$year += 1900;
my $today = sprintf("%04d-%02d-%02d", $year, $mon, $mday);

open LOG, $file or die "Can't open file $file\n$!\n";
my %sum = ();
my $i = 0;
getExistedDate();
extractLog();
outputResult();

sub extractLog {
    my @apps = ('display','common', 'search');
    while (<LOG>) {
        $i++;
        next if $_ !~ /^([\d\.]+) \- \-/;
        $_ =~ /GET \/([a-z]+)\//;
        my $app = $1;
        my %seen;
        foreach my $elm (sort keys %maxhit) {
            if ($app eq $elm) {
                $seen{$app}++;
                last;
            }
        }
        next if ! $seen{$app};
        if ($grouping eq 'day') {
            $_ =~ /^([\d\.]+) \- \- \[(\d\d\/[A-Za-z]{3}\/\d{4})\:\d\d.*\]/;
            $ip = $1;
            $datetime = $2;
        }
        else {
            $_ =~ /^([\d\.]+) \- \- \[(\d\d\/[A-Za-z]{3}\/\d{4}\:\d\d).*\]/;
            $ip = $1;
            $datetime = $2;
        }
        my ($day, $mon, $year) = split('/',$datetime);
        my $Mon = $mon;
        $mon = $mon2num{$mon};
        $mon = sprintf("%02d", $mon);
        $day = sprintf("%02d", $day);
        my $date = $year . '-' . $mon . '-' . $day;
        next if exists $dt{$date.$app};
        next if $date eq $today;
        my $key = $ip . "|" . $app . "|" . $date;
        $ip{$key}++;
        $sum{$date}++;
    }
    close LOG;
}

sub getExistedDate {
    my $stmt = "select dt, app from $tab\n";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
        $dt{$row[0].$row[1]}++;
        print "$row[0]\t$dt{$row[0]}\n";
	}
}

sub outputResult {
    foreach (sort keys %ip){
        if ($_ =~ /^([\d\.]+)\|([a-z]+)\|(.*)$/) {
            my $ip = $1;
            my $app = $2;
            my $dt = $3;
            next if $ip{$_} < $maxhit{$app};
            print "$ip\t$dt\t$app\t$ip{$_} \n";
            &getASPM("insert ignore into $tab (ip, app, dt, count) values ('$ip', '$app', '$dt', $ip{$_})");
        }
    }
}

sub getASPM {
	my $stmt = shift;
	$sth = $dbh->prepare( $stmt ) or die( "\n$stmt\nCannot prepare: ", $dbh->errstr(), "\n" );
	my $rc = $sth->execute() or die("\nDead! \n$stmt\nCannot execute: ", $sth->errstr(),"\n" );
}


