#!/usr/bin/perl
#-- Initial implementation 20171212
#-- Author: Chariya Punyanitya
#-----------------------------
#  get ip statistics by hour

use strict;
use warnings qw(all);
use Dotenv;
Dotenv->load("/webapps/bluenanta/.env");

use Encode qw(encode decode);
use utf8;
use open qw(:locale);
use Time::Piece;

use DBI;
my $DB = $ENV{'DBNAME'};
my $dbh = DBI->connect( "DBI:MariaDB:$DB:$ENV{'DBHOST'}","chariya",$ENV{'MYDBPSSWD'}) or die( "Could not connect to: $DBI::errstr" );
my ($sth, $sth1);
&getASPM("use $DB");


#require "common.pl";
#our ($sth);
my %ip;
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
    species 10 display 100 browse 10 search 10
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
print "getExistedDate\n";
getExistedDate();
print "extractLog\n";
extractLog();
print "outputResult\n";
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
            # print "$app $elm\n"; sleep 1;
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
        # print "{$today $date.$app}\n"; sleep 2;
        # next if $date eq $today;
        my $key = $ip . "|" . $app . "|" . $date;
        $ip{$key}++;
        $sum{$date}++;
        # print "$key: $ip{$key} $sum{$date}\n"; sleep 2;
    }
    # print scalar keys %ip;
    # print "\n";
    close LOG;
}

sub getExistedDate {
    my $stmt = "select dt, app from $tab\n";
    # print "$stmt\n";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
        $dt{$row[0].$row[1]}++;
        # print "$row[0]\t$row[1]\t$dt{$row[0].$row[1]}\n";
	}
}

sub outputResult {
    # print keys %ip;
    foreach (sort keys %ip){
        my ($ip, $app, $dt) = split /\|/, $_;
        next if $ip{$_} < $maxhit{$app};
        print ">$ip\t$dt\t$app\t$ip{$_} \n";
        # &getASPM("insert ignore into $tab (ip, app, dt, count) values ('$ip', '$app', '$dt', $ip{$_})");
    }
}

sub getASPM {
	my $stmt = shift;
	$sth = $dbh->prepare( $stmt ) or die( "\n$stmt\nCannot prepare: ", $dbh->errstr(), "\n" );
	my $rc = $sth->execute() or die("\nDead! \n$stmt\nCannot execute: ", $sth->errstr(),"\n" );
}


