#!/usr/bin/perl

# use strict;
use YAML::XS qw(LoadFile DumpFile);
use HTTP::Tiny;
use Email::Send;
use Email::Send::Gmail;
use Email::Simple::Creator;

my $config_file  = "dynamic_dns.yml";
# my $log_file    = "/var/log/dynamic_dns/dynamic_dns.log";
my $log_filename = "dynamic_dns.log";

open(my $log_fh, '>>', $log_filename) or die "Cannot open log file ($log_filename) for appending.\n$!\n";

my $config = LoadFile($config_file);

sub output {
    my $action = shift;
    my $message = shift;
    my $out = sprintf("%04d-%02d-%02d %02d:%02d:%02d: %s", (localtime)[5]+1900, (localtime)[4]+1, (localtime)[3,2,1,0], sprintf($message, @_));

    print $log_fh $out;

    if($action eq 'warn' or $action eq 'die') {
        my $email = Email::Simple->create(
            header => [
                From    => $config->{config}->{from},
                To      => $config->{config}->{to},
                Subject => sprintf("Dynamic DNS Error: %s", $action),
                ],
            body => sprintf("Dynamic DNS Script %s.\n\n%s.", $action, $out)
            );

        my $sender = Email::Send->new(
            {   mailer      => 'Gmail',
                mailer_args => [
                    username => $config->{config}->{username},
                    password => $config->{config}->{password},
                ]
            }
        );
        $sender->send($email) or warn "Error sending email: $@";
    }

    if($action eq 'warn') { warn $out; }
    elsif($action eq 'die') { die $out; }
    else { print $out; }

    return;
}

foreach my $site (sort keys %{$config->{sites}}) {
    next if($site eq 'config');
    next if($config->{sites}->{$site}->{last_result} eq 'error');

    my $url = sprintf('https://%s:%s@domains.google.com/nic/update?hostname=%s', 
                      $config->{sites}->{$site}->{username}, 
                      $config->{sites}->{$site}->{password},
                      $site);
    my $response = HTTP::Tiny->new->get($url);

    output('warn', 'DNS API call failed.') unless $response->{success};

    if($response->{content} =~ /^(good|nochg)/) {
        output('print', "%s: %s", $site, $response->{content});
    } else {
        $config->{$site}->{sites}->{last_result} = 'error';
        output('warn', "%s: %s", $site, $response->{content});
    }
    print "\n";
}

DumpFile($config_file, $config);
