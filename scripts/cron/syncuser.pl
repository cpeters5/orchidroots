#!/usr/bin/perl
#  This is a cron script used to sync users accounts with photographers
#  getAuthor - get all existing author name into %author
#  getNewUsers - get user's info: userid, fullname, current credit anme and id from email, user and profile
#
use strict;
use warnings FATAL => 'all';
use DateTime;

use DBI;
my $host = '134.209.46.210';
my $db = "bluenanta";
# Database connection
my $dbh = DBI->connect( "DBI:mysql:$db:$host","chariya","Imh#r3r3") or die( "Could not connect to: $DBI::errstr" );
# $dbh = DBI->connect( "DBI:mysql:$db:localhost","chariya","imh3r3r3") or die( "Could not connect to: $DBI::errstr" );
my ($sth, $sth1);
&getASPM("use $db");
my (@user, %author, %credit_name, %credit_name_id, %fullname, %username);
my $id = 0;

getAuthor();

getNewUsers();

setTier();

setAuthor();

setProfile();


sub setTier {
    foreach (@user) {
        my $stmt = "update accounts_user set tier = 2 where id = $_";
        getASPM($stmt);
    }
}

sub setAuthor {
    my $sttime = DateTime->now();
    foreach(@user) {
        if (exists $author{$credit_name_id{$_}}) {
            if ($credit_name{$_}) {
                my $stmt = "update accounts_photographer set
                                displayname = '$credit_name{$_}',
                                fullname = '$fullname{$_}',
                                user_id = $_
                            where author_id = '$credit_name_id{$_}'";
                getASPM($stmt);
                print "$sttime\tUpdate: userid: $_\t$credit_name_id{$_}\t$credit_name{$_}\t$fullname{$_}\n";
                # print "Update photographer, $_ - set displayname = creditname = $credit_name{$_}\n";
            }
            else {
                my $stmt = "update accounts_photographer set
                            displayname = '$fullname{$_}',
                            fullname = '$fullname{$_}'
                            user_id = $_
                            where author_id = '$credit_name_id{$_}'";
                getASPM($stmt);
                # print "Update photographer, set displayname = fullname = $fullname{$_}\n";
                print "$sttime\tUpdate: userid: $_\t$credit_name_id{$_}\t$fullname{$_}\t$fullname{$_}\n";
           }
        }
        else {
            if ($credit_name{$_}) {
                my $stmt = "insert into accounts_photographer (user_id, fullname, displayname, author_id)
                            values($_, '$fullname{$_}', '$credit_name{$_}', '$credit_name_id{$_}')";
                getASPM($stmt);
                print "$sttime\tCreate: userid: $_\t$credit_name_id{$_}\t$credit_name{$_}\t$fullname{$_}\n";
                # print "Create photographer, $_ - fullname = $fullname{$_}, display = $credit_name{$_}, userid = $credit_name_id{$_}  \n";
            }
            else {
                my $stmt = "insert into accounts_photographer (user_id, fullname, displayname, author_id)
                            values($_, '$fullname{$_}', '$fullname{$_}', '$credit_name_id{$_}')";
                getASPM($stmt);
                print "$sttime\tCreate: userid: $_\t$credit_name_id{$_}\t$fullname{$_}\t$fullname{$_}\n";
                # print "Create photographer, $_ - fullname = $fullname{$_} = displaynamed = $fullname{$_}, userid = $credit_name_id{$_}  \n";
            }

        }
    }
}

sub setProfile {
    foreach (@user) {
        if ($credit_name{$_}) {
            my $stmt = "update accounts_profile set current_credit_name_id = '$credit_name_id{$_}', profile_pic = 'DONE'
                        where user_id = '$_'";
            getASPM($stmt);
        }
        else {
            my $stmt = "update accounts_profile set current_credit_name_id = '$credit_name_id{$_}', photo_credit_name = '$fullname{$_}', profile_pic = 'DONE'
                        where user_id = '$_'";
            getASPM($stmt);
        }
    }
}

sub getNewUsers {
    my $stmt = "SELECT a.user_id, b.fullname, b.username, c.photo_credit_name, c.current_credit_name_id
                FROM `account_emailaddress` a
                join accounts_user b on a.user_id = b.id
                join accounts_profile c on a.user_id = c.user_id
                where b.tier = 1 and a.verified = 1 order by a.user_id;";
    &getASPM($stmt);
    while (my @row = $sth->fetchrow_array()) {
    	push(@user, $row[0]);
        $fullname{$row[0]} = $row[1] if $row[1];
        $row[2] =~ s/ //g;

        $credit_name{$row[0]} = $row[3] if $row[3];
        if ($row[4]) {
            $credit_name_id{$row[0]} = $row[4];
        }
        else {  # no credit anme given, try to use login id
            my $username = $row[2];
            $username =~ /^(.*)@/;
            $username = $1 if $1;
            $credit_name_id{$row[0]} = $username;
            my @Chars = ('1'..'9');
            my $Length = 10;
            my $Number = '';

            for (1..$Length) {
                last if not exists $author{$credit_name_id{$row[0]}};
                $credit_name_id{$row[0]} .= $Chars[int rand @Chars];
            }
        }
    }
}

sub getAuthor {
    my $stmt = "Select author_id from accounts_photographer";
    &getASPM($stmt);
    while (my @row = $sth->fetchrow_array()) {
        $author{$row[0]}++;
    }
}


sub getASPM {
	my $stmt = shift;
	$sth = $dbh->prepare( $stmt ) or die( "\n$stmt\nCannot prepare: ", $dbh->errstr(), "\n" );
	my $rc = $sth->execute() or die("\nDead! \n$stmt\nCannot execute: ", $sth->errstr(),"\n" );
}
