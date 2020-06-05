#!/bin/sh
(cd /usr/lib && sudo babel /picoCTF/picoCTF-web/web/jsx -d /picoCTF/picoCTF-web/web/js --presets=@babel/preset-env,@babel/preset-react)
sudo jekyll build -s /picoCTF/picoCTF-web/web
