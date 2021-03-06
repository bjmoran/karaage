Getting Started
===============
This section is for administrators who don’t already have Karaage installed and
wish to get started for the first time.

If you do have an older version of Karaage already installed, please see the
:doc:`upgrading` section.


Assumptions
-----------
Assumptions made by this documentation. Other configurations are possible,
however you will have to adapt from this documentation.

* You have a cluster running Slurm or PBS that is already up and running.
* You want to OpenLDAP with ppolicy support, on the same server.
* You have a Debian Jessie server already setup for Karaage.
* You will be installing all components on a single system.
* You are upgrading to Karaage 3.1.
* The visible hostname is ``www.example.org``. This will have to be
  changed as required.
* Note these instructions install the shibboleth support, which may not
  be required. Simplifications can be made to some steps if shibboleth
  not required.


MySQL configuration
-------------------

#.  Run the following commands:

    .. code-block:: bash

        apt-get install mysql-server

    This should ask for a password for the root mysql user. Make sure this is a
    secure password. You can use makepasswd if you want. For the purpose of
    this documentation, we will assume you used ``XXXXXXXX``. Do not use
    ``XXXXXXXX`` for your password on a production system.

#.  (optional) Create a ``/root/.my.cnf`` file containing::

        [client]
        user            = root
        password        = XXXXXXXX

#.  Create a ``/etc/mysql/conf.d/karaage.cnf`` file containing::

        [mysqld]
        character_set_server=utf8
        default-storage-engine = innodb
        sql_mode = STRICT_ALL_TABLES

        [client]
        default-character-set = utf8

    Note: these settings may affect other applications that use this database.

#.  Restart mysql server to load config, and connect to it:

    .. code-block:: bash

        service mysql restart
        mysql

#.  Create a user and database for karaage::

        mysql> create database karaage;
        mysql> CREATE USER 'karaage'@'localhost' IDENTIFIED BY 'YYYYYYYY';
        mysql> GRANT ALL PRIVILEGES ON karaage.* TO 'karaage'@'localhost';

    You will use the values you set, later, in the karaage settings. Do not use
    ``YYYYYYYY`` on a production system.


Installation
------------
#.  If you require a proxy server for out going connections, set it up now.

    .. code-block:: bash

        export http_proxy=http://proxy.example.org

#.  Create `/etc/systemd/system/karaage.service` file::

        [Unit]
        Description=Karaage
        After=docker.service
        Requires=docker.service

        [Service]
        TimeoutStartSec=0
        ExecStartPre=-/usr/bin/docker kill karaage
        ExecStartPre=-/usr/bin/docker rm karaage
        ExecStartPre=/usr/bin/docker pull brianmay/karaage:slurm17.02-apache
        ExecStart=/usr/bin/docker run --name karaage \
          --net="host" \
          -v /etc/passwd:/etc/passwd \
          -v /etc/group:/etc/group \
          -v /opt/karaage/etc/munge:/etc/munge \
          -v /opt/karaage/log/munge:/var/log/munge \
          -v /opt/karaage/lib/munge:/var/lib/munge \
          -v /opt/karaage/etc/slurm:/usr/local/etc \
          -v /opt/karaage/etc/shibboleth:/etc/shibboleth \
          -v /opt/karaage/etc/karaage3:/etc/karaage3 \
          -v /opt/karaage/log/apache2:/var/log/apache2 \
          -v /opt/karaage/log/karaage3:/var/log/karaage3 \
          -v /opt/karaage/lib/karaage3:/var/lib/karaage3 \
          -v /opt/karaage/cache/karaage3:/var/cache/karaage3 \
          brianmay/karaage:slurm17.02-apache
        ExecStop=/usr/bin/docker stop karaage

        [Install]
        WantedBy=multi-user.target


#.  Create required users in ``/etc/passwd``:

    *  ``munge``: required for munge, for slurm.
    *  ``_shibd``: required for shibbioleth.
    *  ``www-data``: required by web process.

#.  Create required directories and configuration files:

    * ``/opt/karaage/etc/munge``: contains ``munge.key``, and must be
      owned and only readable by ``munge`` user.
    * ``/opt/karaage/log/munge``: should be writable by ``munge`` user.
    * ``/opt/karaage/lib/munge``: should be writable by ``munge`` user.
    * ``/opt/karaage/etc/slurm``: should contain ``slurm.conf``.
    * ``/opt/karaage/etc/shibboleth``: should contain all shibboleth config.
    * ``/opt/karaage/etc/karaage3``: should contain ``settings.py``.
    * ``/opt/karaage/log/apache2``: Should be writable by ``www-data``.
    * ``/opt/karaage/log/karaage3``: Should be writable by ``www-data``.
    * ``/opt/karaage/lib/karaage3``: Should be writable by ``www-data``.
    * ``/opt/karaage/cache/karaage3``: Should be writable by ``www-data``.

#.  Copy ``/etc/karaage3/settings.py`` from initial sample file.
#.  Edit the :setting:`DATABASES` setting in ``/etc/karaage3/settings.py``:

    .. code-block:: python

         DATABASES = {
              'default': {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': 'karaage',
                    'USER': 'karaage',
                    'PASSWORD': 'YYYYYYYY',
                    'HOST': 'localhost',
                    'PORT': '',
                    'ATOMIC_REQUESTS': True,
                    'OPTIONS': {
                        'sql_mode': 'STRICT_ALL_TABLES'
                    },
              }
         }

#.  Add the :setting:`HTTP_HOST` setting in ``/etc/karaage3/settings.py``:

    .. code-block:: python

        HTTP_HOST = "www.example.org"

    Replace ``www.example.org`` with the visible hostname of your server.

#.  Update other settings in ``/etc/karaage3/settings.py`` as required. See
    comments in this file and :doc:`/ref/settings`.

#.  Restart Karaage after changing ``/etc/karaage3/settings.py``.

    .. code-block:: bash

        systemctl restart karaage

#.  Create a karaage superuser using :djadmin:`kgcreatesuperuser`:

    .. code-block:: bash

        kg-manage kgcreatesuperuser

#.  Start karaage.

    .. code-block:: bash

        systemctl daemon-reload
        systemctl start karaage

#.  Monitor progress of Karaage starting.

    .. code-block:: bash

        journalctl -u karaage -f

#.  Check that Karaage is running and listening on http://localhost:443/.



SSL certificate
---------------
You should create a signed SSL certificate for Apache and LDAP.

#.  Generate a SSL private key, a CSR.

    .. code-block:: bash

        cd /etc/ssl/private
        openssl genrsa -out www_privatekey.pem 2048
        chmod 640 www_privatekey.pem
        openssl req -new -key www_privatekey.pem -out www_csr.pem -sha256

#.      Submit www_csr.pem to a CA, and get it signed. Copy resultant
        certificate into ``www_cert.pem``. Check this file is sha256:

        .. code-block:: bash

            openssl x509 -text -noout -in www_cert.pem

        You should see the following text::

            Signature Algorithm: sha256WithRSAEncryption.

        You may need an intermediate certificate too. Copy this into
        ``www_intermediate.pem``.

#.  Join certificate with intermediate (required for some versions of slapd):

    .. code-block:: bash

        cd /etc/ssl/private
        cat www_cert.pem www_intermediate.pem > www_combined.pem

#.  Setup the permissions:

    .. code-block:: bash

        apt-get install ssl-cert
        cd /etc/ssl/private
        chown root:ssl-cert www_*.pem

..  todo::

    OS other then Debian may not have ssl-cert group, e.g. CentOS 6.6 doesn't.
    The above instructions will not work.


Apache Configuration
--------------------
Karaage, by default, requires a https connection. While this default can be
changed, this is not advisable on a production system.

In the following steps, replace ``www.example.org`` with the visible hostname
of your server.

#.  Install apache2.

    .. code-block:: bash

        apt-get install apache2

#.  Setup Apache to support secure https connections. Changes should be
    made to ``/etc/apache2/sites-available/default-ssl``::

        SSLCertificateFile /etc/ssl/private/www_cert.pem
        SSLCertificateKeyFile /etc/ssl/private/www_privatekey.pem
        SSLCertificateChainFile /etc/ssl/private/www_intermediate.pem

    For more details on what changes are required, see the `Apache howto
    <http://httpd.apache.org/docs/current/ssl/ssl_howto.html>`_.

#.  Connections to http should be redirected to https.  Please replace the
    ``/etc/apache2/sites-available/default`` file entirely with the
    following::

        <VirtualHost *:80>
            ServerName www.example.org
            Redirect permanent / https://www.example.org/
        </VirtualHost>

    For more information on this step,
    see the `Apache wiki <https://wiki.apache.org/httpd/RedirectSSL>`_.

#.  (recommended) It is recommended that you change the following settings in
    ``/etc/apache2/mods-available/ssl.conf`` to make SSL more secure by
    disabling insecure protocols and ciphers::

       SSLProtocol all -SSLv2 -SSLv3
       SSLCipherSuite ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA

    Note however that the ``SSLProtocol`` will break IE6, and the
    ``SSLCipherSuite`` setting will break IE on XP. For more information on
    securing Apache, see the `Mozilla website
    <https://wiki.mozilla.org/Security/Server_Side_TLS>`_.

#.  Enable ``default-ssl`` with the following commands:

    .. code-block:: bash

        a2enmod ssl
        a2ensite default-ssl.
        service apache2 restart

#.  Test by loading both ``http://www.example.org/`` and
    ``https://www.example.org/`` in your browser.

#.  (recommended) Enable
    `HSTS <https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security>`_
    support with the following commands:

    .. code-block:: bash

        echo 'Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"' > /etc/apache2/conf-available/hsts.conf
        a2enmod  headers
        a2enconf hsts
        service apache2 restart

#.  Test by loading both ``http://www.example.org/`` and
    ``https://www.example.org/`` in your browser.

#.  Test website with `SSL Test
    <https://www.ssllabs.com/ssltest/index.html>`_.

#.  Enable proxy with the following commands:

    .. code-block:: bash

        a2enmod proxy proxy_http
        service apache2 restart

#.  Add following to `/etc/apache2/sites-available/000-default.conf`::

        <Location "/Shibboleth.sso/">
            ProxyPreserveHost On
            ProxyPass "http://localhost:443/Shibboleth.sso/"
            ProxyPassReverse "http://localhost:443/Shibboleth.sso/"
        </Location>
        Alias /kgstatic "/var/lib/karaage3/static"
        <Location "/kgstatic">
            SetHandler None
            Require all granted
        </Location>
        <Location "/karaage/">
            ProxyPreserveHost On
            ProxyPass "http://localhost:443/karaage/"
            ProxyPassReverse "http://localhost:443/karaage/"
        </Location>


Data stores
-----------
So far you have not configured any external datastores. Karaage will work,
however probably won’t do anything useful. See the next section to configure
datastores (:doc:`datastores`).


Plugins
-------
For information on configuring additional plugins, see :doc:`plugins`.


Cluster tools
-------------
If installing Karaage on a cluster, you may want to install the cluster tools,
see :doc:`cluster`.
