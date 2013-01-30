
SELENIUM_DOWNLOAD_URL="http://selenium.googlecode.com/files/selenium-server-standalone-2.29.0.jar"
SELENIUM_EXECUTABLE_SHA1="fe8c13da809f8c2dd0a84fd082cea3e4f0596b7e"
SELENIUM_EXECUTABLE="$TMP/selenium-server-standalone-2.25.0.jar"

SELENIUM_CONFIG="$(dirname $0)/selenium_config.json"

SELENIUM_DOWNLOADER_LOCK="$TMP/selenium-downloader.lock"

function check_sha1(){
    # $1 - file path
    # $2 - sha1
    if [ ! -f $1 ];then
        return 1
    fi

    SHA1=$(sha1sum "$1"|cut -f1 -d' ')
    if [ "$2" == "$SHA1" ];then
        return 0
    fi
    return 1
}

function cache_selenium(){
    echo " * If there are any errors with downloading try to remove lock in $SELENIUM_DOWNLOADER_LOCK"
    while [ -f "$SELENIUM_DOWNLOADER_LOCK" ];
    do
        echo " * Waiting until another process download selenium (lock in $SELENIUM_DOWNLOADER_LOCK)"
        sleep 5
    done

    if [ ! -f "$SELENIUM_EXECUTABLE" ];then
        echo " * downloading selenium to $SELENIUM_EXECUTABLE..."
        touch "$SELENIUM_DOWNLOADER_LOCK"
        if ! wget --quiet "$SELENIUM_DOWNLOAD_URL" -O "$SELENIUM_EXECUTABLE" ;then
            echo "There were errors during downloading selenium..."
            rm "$SELENIUM_EXECUTABLE"
        fi
        rm "$SELENIUM_DOWNLOADER_LOCK"
    else
        echo " * selenium exists in $SELENIUM_EXECUTABLE"
    fi

    if check_sha1 "$SELENIUM_EXECUTABLE" "$SELENIUM_EXECUTABLE_SHA1" ;then
        echo " + SHA1 OK"
        return 0
    fi

    echo " - SHA1 FAILED"
    return 1
}
