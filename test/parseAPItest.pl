#!/usr/bin/perl
use LWP::Simple;
use LWP::UserAgent;
use LWP::Protocol::https;
use HTTP::Request::Common;
use Data::Dumper;
use JSON;


my  $ua = LWP::UserAgent->new();
$ua->timeout(3);

my $sessionID  = 'ciao';

my $url="http://127.0.0.1:5000/api/parse";
my $URI_START_SESSION = 'http://127.0.0.1:5000/api/startSession/' . $sessionID;


my $sourceLanguage = 'en';
my @targetTanguages = ('es', 'fr');

#initiating a session
my $answer = get($URI_START_SESSION);
print "Session: " . $answer . "\n";

#going trough a file
my $file = 'Enunciated.txt';
open my $info, $file or die "Could not open $file: $!";

while( my $line = <$info>)  {   
    print "Sending ASR: $line";
    my $status = "final";
    my $text   = "empty";

    my @fields = split (/\t/,$line);


    if ($fields[1] eq 'True'){
        $status = 'final';
    }else{
        $status = 'temporary'
    }
    my $text = $fields[0];

    my $data = { asr => $text, status => $status, room => $sessionID, sourceLanguage => $sourceLanguage, targetLanguages => \@targetTanguages};

    my $data_json = encode_json($data);	

    my $request  = POST($url, Content_Type=>'application/json',
                    Content  => encode_json($data) );
    my $res = $ua->request($request);

                if ($res->is_success) {
                    my $json_text= $res->content; 
                    print "\n$json_text\n\n";
                    eval {
                        my $data = decode_json( $json_text );
                    };
                    if ($@) {
                    }
                }
        else{
            print "Error connecting to the server\n";
        }
}

1;