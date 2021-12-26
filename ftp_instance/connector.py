import ftplib
import pickle
from io import BytesIO


class Connector(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.credentials = host, username, password
        self.file_list = None
    
    def get_connection(self):
        return ftplib.FTP(*self.credentials)
    
    def set_dir(self, path):
        with self.get_connection() as ftp:
            try:
                ftp.cwd(path)
                return True
            except ftplib.all_errors as e:
                raise ConnectionError("FTP error:", e)
        return False
    
    def get_files(self):
        with self.get_connection() as ftp:
            try:
                return list(ftp.mlsd())
            except ftplib.all_errors as e:
                raise ConnectionError("FTP error:", e)
    
    def file_exists(self, filename, refresh=False):
        if not self.file_list or refresh:
            with self.get_connection() as ftp:
                try:
                    self.file_list = ftp.nlst()
                except ftplib.all_errors as e:
                    raise ConnectionError("FTP error:", e)
        return filename in self.file_list
    
    def store_instance(self, instance, filename):
        instance_pickle = pickle.dumps(instance)
        with BytesIO(instance_pickle) as buffer:
            with self.get_connection() as ftp:
                try:
                    ftp.storbinary(f"STOR {filename}", buffer)
                    return True
                except ftplib.all_errors as e:
                    raise ConnectionError("FTP error:", e)
        return False
    
    def load_instance(self, filename):
        with BytesIO() as buffer:
            with self.get_connection() as ftp:
                try:
                    ftp.retrbinary(f"RETR {filename}", buffer.write)
                    instance = pickle.loads(buffer.getvalue())
                    return instance
                except ftplib.all_errors as e:
                    raise ConnectionError("FTP error:", e)
