function download
    set url $argv[1]
    yt-dlp -f 'ba' -x --audio-format mp3 $url -o '%(title|replace:/,:)%'
end