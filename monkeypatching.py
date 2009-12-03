import os
import StringIO
import mimetypes

from socket  import timeout
from urllib  import quote

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import cloudfiles

class BackObject(cloudfiles.storage_object.Object):
    """
    Allow to exit when the callback set to False
    """
    def _get_conn_for_write(self):
        headers = self._make_headers()

        headers['X-Auth-Token'] = self.container.conn.token

        path = "/%s/%s/%s" % (self.container.conn.uri.rstrip('/'), \
                quote(self.container.name), quote(self.name))

        # Requests are handled a little differently for writes ...
        http = self.container.conn.connection

        # TODO: more/better exception handling please
        http.putrequest('PUT', path)
        for hdr in headers:
            http.putheader(hdr, headers[hdr])
        http.putheader('User-Agent', cloudfiles.consts.user_agent)
        http.endheaders()
        return http

    def write(self, data='', verify=True, callback=None):
        """
        Write data to the remote storage system.

        By default, server-side verification is enabled, (verify=True), and
        end-to-end verification is performed using an md5 checksum. When
        verification is disabled, (verify=False), the etag attribute will
        be set to the value returned by the server, not one calculated
        locally. When disabling verification, there is no guarantee that
        what you think was uploaded matches what was actually stored. Use
        this optional carefully. You have been warned.

        A callback can be passed in for reporting on the progress of
        the upload. The callback should accept two integers, the first
        will be for the amount of data written so far, the second for
        the total size of the transfer.

        >>> test_object = container.create_object('file.txt')
        >>> test_object.content_type = 'text/plain'
        >>> fp = open('./file.txt')
        >>> test_object.write(fp)

        @param data: the data to be written
        @type data: str or file
        @param verify: enable/disable server-side checksum verification
        @type verify: boolean
        @param callback: function to be used as a progress callback
        @type callback: callable(transferred, size)
        """
        self._name_check()
        if isinstance(data, file):
            # pylint: disable-msg=E1101
            try:
                data.flush()
            except IOError:
                pass # If the file descriptor is read-only this will fail
            self.size = int(os.fstat(data.fileno())[6])
        else:
            data = StringIO.StringIO(data)
            self.size = data.len

        # If override is set (and _etag is not None), then the etag has
        # been manually assigned and we will not calculate our own.

        if not self._etag_override:
            self._etag = None

        if not self.content_type:
            # pylint: disable-msg=E1101
            type = None
            if hasattr(data, 'name'):
                type = mimetypes.guess_type(data.name)[0]
            self.content_type = type and type or 'application/octet-stream'

        http = self._get_conn_for_write()

        response = None
        transfered = 0
        running_checksum = md5()

        buff = data.read(4096)
        try:
            while len(buff) > 0:
                http.send(buff)
                if verify and not self._etag_override:
                    running_checksum.update(buff)
                buff = data.read(4096)
                transfered += len(buff)
                if callable(callback):
                    ret = callback(transfered, self.size)
                    if not ret:
                        return "Aborted"
            response = http.getresponse()
            buff = response.read()
        except timeout, err:
            if response:
                # pylint: disable-msg=E1101
                buff = response.read()
            raise err
        else:
            if verify and not self._etag_override:
                self._etag = running_checksum.hexdigest()

cloudfiles.storage_object.Object = BackObject
