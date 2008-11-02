"""
mp3players

Contains objects encapsulating methods to manage adding tracks
to audio players.
"""
import sys, os, os.path, re

def main():
    p = iTunesMac()
    p.addTrack(sys.argv[1])

class iTunesMac:
    OSASCRIPT = '/usr/bin/osascript'
    
    ADD_TRACK_SCRIPT = """
    property arguments : "%s"

    -- Derive a Mac-style path from a given POSIX path.
    set track_path to arguments
    set track_file to POSIX file track_path

    -- Launch iTunes as hidden, if not already running.
    tell application "System Events"
        if not (exists process "iTunes") then
            tell application "iTunes"
                launch
                set visible of front window to false
            end tell
        end if
    end tell

    tell application "iTunes"
        -- Import the new track into main library.
        set this_track to add track_file to playlist "library" of source "library"
        set the genre of this_track to "Podcast"

        -- Create the "Podcasts" playlist if needed, add new track to it.
        if not (exists user playlist "Podcasts" of source "library") then
            make new playlist of source "library" with properties {name:"Podcasts"}
        end if
        duplicate this_track to playlist "Podcasts" of source "library"
                                
        -- This might fail if no iPod is connected
        try
            -- Find an iPod
            set the_iPod to some source whose kind is iPod

            -- Copy the new track to the iPod main library
            duplicate this_track to playlist 1 of the_iPod

            -- Create the "Podcasts" playlist if needed, add new track to it.
            if not (exists user playlist "Podcasts" of the_iPod) then
                make new playlist of the_iPod with properties {name:"Podcasts"}
            end if
            duplicate this_track to playlist "Podcasts" of the_iPod
        end try

    end tell
    """
    
    def _executeAppleScript(self, script): 
        """ Given the text of an AppleScript, attempt to execute it.  """
        fi = os.popen(self.OSASCRIPT, "w")
        fi.write(script)
        fi.close()

    def addTrack(self, fn):
        abs_fn = os.path.abspath(fn)
        self._executeAppleScript(self.ADD_TRACK_SCRIPT % abs_fn)
    
if __name__=='__main__': main()
