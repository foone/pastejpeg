# pastejpeg
 Converts a PNG on the windows clipboard into a JPEG you can paste.
 I developed this to let me paste out of Paint.NET into mastodon, without the images ending up uploaded as very large PNG files. 

# Usage

Simply run pastejpeg.py with Python 3.x with a PNG on the clipboard. It'll be saved out to a JPEG file, then the path of the JPEG will be copied. Then you can paste it into a browser, and it'll upload as a JPEG, not a PNG. 
Optionally pass --gui and you'll get errors (other than "there's no PNG on the clipboard") as message boxes, not command line messages. 

Note that if the JPEG it would have copied ends up bigger than the source PNG, the PNG will remain on the clipboard.

# Testing

I have only tested this with Chrome, Mastodon, and Paint.NET. It is entirely possible it doesn't work elsewhere

# Requirements

* Python 3.x (Tested with 3.11.0)
* ImageMagick (tested with 7.0.8-27)
  (ImageMagick is looked up in the path using the "magick" alias, to avoid the "convert" collision.)

# License
GPL v3