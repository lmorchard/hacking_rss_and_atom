#!/usr/bin/env python
"""
downloaders.py

Provides means to download content by URL.
"""
import sys, os.path, urllib2, time
from urlparse import urlparse

from threading import Event
from BitTorrent.bencode import bdecode
import BitTorrent.download
    
def main():
    """
    Test a downloader.
    """
    url = "http://homepage.mac.com/adamcurry/Default/podcastDefaultWelcome.mp3"
    dl = HTTPDownloader()
    files = dl.downloadURL(".", url)
    print "\n".join(files)
    
class HTTPDownloader:
    """
    This provides a simple HTTP content downloader.
    """
    PERC_STEP  = 10
    CHUNK_SIZE = 10*1024
    PROG_OUT   = sys.stdout
    
    def _print(self, msg):
        self.PROG_OUT.write(msg)
        self.PROG_OUT.flush()
        
    def downloadURL(self, dest_path, url):
        """
        Given a destination path and URL, download with a 
        progress indicator.
        """
        files = []
        
        # Dissect the given URL to extract a filename, build output path.
        url_path  = urlparse(url)[2]
        url_fn    = os.path.basename(url_path)
        fout_path = os.path.join(dest_path, url_fn)
        files.append(fout_path)
        self._print("\t\t%s" % (url_fn))
        
        # Open the file for writing, initialize size to 0.
        fout      = open(fout_path, "w")
        fout_size = 0
        
        # Open the URL for reading, try getting the content length.
        fin          = urllib2.urlopen(url)
        fin_size_str = fin.headers.getheader("Content-Length", "-1")
        fin_size     = int(fin_size_str.split(";",1)[0])
        self._print(" (%s bytes): " % (fin_size))
        
        # Initialize variables tracking download progress
        perc_step, perc, next_perc = self.PERC_STEP, 0, 0
        perc_chunk = fin_size / (100/self.PERC_STEP) 
        
        while True:
            # Read in a chunk of data, breaking from loop if 
            # no data returned
            data = fin.read(self.CHUNK_SIZE)
            if len(data) == 0: break
            
            # Write a chunk of data, incrementing output file size
            fout.write(data)
            fout_size += len(data)
             
            # If the current output size has exceeded the next
            while fin_size > 0 and fout_size >= next_perc:
                self._print("%s " % perc)
                perc      += perc_step
                next_perc += perc_chunk
            
        # Close input & output, line break at the end of progress.
        fout.close()
        fin.close()
        self._print("\n")

        return files

class BitTorrentDownloader:
    """
    This provides a simple BitTorrent downloader, with an optional
    post-download seeding function.
    """
    PERC_STEP     = 10
    START_TIMEOUT = 15
    SEED_TORRENT  = True
    SEED_TIME     = 20 * 60 # 20 minutes
    PROG_OUT      = sys.stdout
    
    def downloadURL(self, dest_path, url):
        """
        Given the URL to a BitTorrent .torrent, attempt to download
        the content.
        """
        # Initialize some state attributes.
        self._stop        = Event()
        self._init_time   = time.time()
        self._start_time  = None
        self._finish_time = None
        self._next_perc   = 0.0
        self._dest_path   = dest_path
        
        # Get the list of files and total length from torrent
        name, files, total_length = self._getTorrentMeta(dest_path, url)

        # Display name of file or dir in torrent, along with size
        self._print("\t\t%s (%s bytes): " % (name, total_length))

        # Run the BitTorrent download
        BitTorrent.download.download(['--url', url], self._choose, 
                self._display, self._fin, self._error, self._stop, 80)
        
        # Finish off the progress display, return the list of files
        self._print("\n")
        return files

    def _getTorrentMeta(self, dest_path, url):
        """
        Given the download destination path and URL to the torrent,
        extract the metadata to return the torrent file/dir name,
        files to be downloaded, and total length of download.
        """
        # Grab the torrent metadata
        metainfo_file = urllib2.urlopen(url)
        metainfo = bdecode(metainfo_file.read())
        metainfo_file.close()
        
        # Gather the list of files in the torrent and total size.
        files = []
        info = metainfo['info']
        if not info.has_key('files'):
            # Get the length and path of the single file to download.
            total_length = info['length']
            files.append(os.path.join(dest_path, info['name']))
        else:
            # Calculate the total length and find paths of all files
            # to be downloaded.
            total_length = 0
            files_root   = os.path.join(dest_path, info['name'])
            for file in info['files']:
                total_length += file['length']
                file_path = os.path.join(*(file['path']))
                files.append(os.path.join(files_root, file_path))

        return info['name'], files, total_length
    
    def _print(self, msg):
        """Print an immediate status message."""
        self.PROG_OUT.write(msg)
        self.PROG_OUT.flush()
        
    def _fin(self):
        """Handle the completion of file download."""
        if not self.SEED_TORRENT:
            # Stop if not opting to seed the torrent.
            self._stop.set()
        else:
            # Note the finish time and print notification of seeding.
            self._finish_time = time.time()
            self._print("SEEDING")
        
    def _choose(self, default, size, saveas, dir):
        """Prepend the destination path onto the download filename."""
        return os.path.join(self._dest_path, default)

    def _error(self, message):
        """Handle displaying errors."""
        self._print("[ ERROR: %s ]" % message)

    def _display(self, disp):
        """
        Display status event handler.  Takes care of tracking stalled
        and started downloads, progress indicator updates, as well as
        seeding the torrent after download.
        """
        # Check download rate to detect download start.
        if disp.has_key('downRate'):
            if not self._start_time and disp['downRate'] > 0.0:
                self._start_time = time.time()

        # Check to see if the download's taken too long to start.
        if not self._start_time:
            init_wait = (time.time() - self._init_time)  
            if init_wait > self.START_TIMEOUT:
                self._print("timeout before download start")
                self._stop.set()
    
        # Handle progress display, if fractionDone present. 
        if disp.has_key('fractionDone'):
            perc_done = disp['fractionDone'] * 100.0
            while perc_done > self._next_perc:
                self._print("%d " % self._next_perc)
                self._next_perc += self.PERC_STEP

        # Handle completed download and seeding conditions.
        if self._finish_time:
            # Stop if no one's downloading from us.
            if disp.has_key('upRate') and not disp['upRate'] > 0.0:
                self._stop.set()
            
            # Stop if we've uploaded as much or more than we downloaded.
            if disp.has_key('upTotal') and disp.has_key('downTotal') and \
                    disp['upTotal'] >= disp['downTotal']:
                self._stop.set()
                
            # Stop if we've been seeding for too long.
            seed_time = time.time() - self._finish_time
            if seed_time >= self.SEED_TIME: 
                self._stop.set()

if __name__=='__main__': main()
