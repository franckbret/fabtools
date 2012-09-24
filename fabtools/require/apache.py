"""
Idempotent API for managing apache sites
"""
from __future__ import with_statement

from fabric.api import *
from fabric.colors import red
from fabtools.files import upload_template, is_link
from fabtools.require.deb import package
from fabtools.require.files import template_file
from fabtools.require.service import started, restarted

def server():
    """
    Require apache2 server to be installed and running.

    ::

        from fabtools import require
        require.apache2.server()
    """
    package('apache2')
    started('apache2')


def site(server_name, template_contents=None, template_source=None, enabled=True, check_config=True, **kwargs):
    """
    Require an apache2 site.

    You must provide a template for the site configuration, either as a
    string (*template_contents*) or as the path to a local template
    file (*template_source*).

    ::

        from fabtools import require

        VHOST_SITE_TEMPLATE = '''
        NameVirtualHost %(server_name)s:%(port)s
        <VirtualHost %(server_name)s:%(port)s>
          ServerName %(server_name)s
          ServerAdmin webmaster@%(server_name)s
          DocumentRoot %(docroot)s
          <Directory %(docroot)s>
            AllowOverride all
            Order allow,deny
            allow from all
          </Directory>
          ErrorLog /var/log/apache2/%(server_name)s.error.log
          CustomLog /var/log/apache2/%(server_name)s.access.log combined
          LogLevel warn
          ServerSignature Off
        </VirtualHost>
        '''

        require.apache2.site('example.com', template_contents=VHOST_SITE_TEMPLATE,
                port=80,
                server_alias='www.example.com',
                docroot='/var/www/mysite',
            )
        )

    .. seealso:: :py:func:`fabtools.require.files.template_file`
    """

    server()

    config_filename = '/etc/apache2/sites-available/%s.conf' % server_name

    context = {
        'port': 80,
    }
    context.update(kwargs)
    context['server_name'] = server_name

    template_file(config_filename, template_contents, template_source, context, use_sudo=True)

    link_filename = '/etc/apache2/sites-enabled/%s.conf' % server_name
    if enabled:
        if not is_link(link_filename):
            sudo("ln -s %(config_filename)s %(link_filename)s" % locals())
        # Make sure we don't break the config
        if check_config:
            with settings(hide('running', 'warnings'), warn_only=True):
                if not sudo("apache2ctl configtest" % locals()) == "Syntax OK":
                    print red("Error in %(server_name)s apache2 site config (disabling for safety)" % locals())
                    sudo("rm %(link_filename)s" % locals())
    else:
        if is_link(link_filename):
            sudo("rm %(link_filename)s" % locals())

    restarted('apache2')

def activate_module(module):
    """ 
    Activate an Apache module.
    Be sure to restart apache for changes to take effect.

    ::
    
        from fabtools.require.service import restarted

        apache_modules_activate = ['suexec', 'actions', 'headers', 'include', 'deflate', 'mem_cache', 'rewrite', 'env']

        for module in apache_modules_activate:
            fabtools.require.apache.activate_module(module) 

        restarted('apache2')

    """
    with settings(hide('running', 'warnings'), warn_only=True):
        sudo("a2enmod %s" % module)

def deactivate_module(module):
    """ 
    Desactivate an Apache module, be sure to restart apache for changes to take effect.
    ::
    
        from fabtools.require.service import restarted

        apache_modules_deactivate = ['autoindex', 'cgi', 'default']

        for module in apache_modules_deactivate:
            fabtools.require.apache.deactivate_module(module) 

        restarted('apache2')
    """
    with settings(hide('running', 'warnings'), warn_only=True):
        sudo("a2dismod %s" % module)