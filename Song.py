class Song:

    def __init__(self, title, artist, album, length):
        self.url = None
        self.prompt = ""
        self.album = album
        self.title = title
        self.artist = artist
        self.length = length
        self.downloaded = False

    def __repr__(self):
        return self.prompt

    def get_title(self):
        return self.title

    def get_artist(self):
        return self.artist

    def get_album(self):
        return self.album

    def get_url(self):
        return self.url

    def get_length(self):
        return self.length

    def get_prompt(self):
        return self.prompt

    def set_url(self, url):
        self.url = url

    def set_prompt(self, prompt):
        self.prompt = prompt

    def set_downloaded(self, status):
        self.downloaded = status

    def get_downloaded(self):
        return self.downloaded

    def set_length(self, len):
        self.length = len
