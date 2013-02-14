#!/usr/bin/python

# Common python helper functions used for OpenStack charms.

import subprocess

CLOUD_ARCHIVE_URL = "http://ubuntu-cloud.archive.canonical.com/ubuntu"
CLOUD_ARCHIVE_KEY_ID = '5EDB1B62EC4926EA'

ubuntu_openstack_release = {
    'oneiric': 'diablo',
    'precise': 'essex',
    'quantal': 'folsom',
    'raring': 'grizzly'
}


openstack_codenames = {
    '2011.2': 'diablo',
    '2012.1': 'essex',
    '2012.2': 'folsom',
    '2012.3': 'grizzly'
}


def juju_log(msg):
    subprocess.check_call(['juju-log', msg])


def error_out(msg):
    juju_log("FATAL ERROR: %s" % msg)
    exit(1)


def lsb_release():
    '''Return /etc/lsb-release in a dict'''
    lsb = open('/etc/lsb-release', 'r')
    d = {}
    for l in lsb:
        k, v = l.split('=')
        d[k.strip()] = v.strip()
    return d


def get_os_codename_install_source(src):
    '''Derive OpenStack release codename from a given installation source.'''
    ubuntu_rel = lsb_release()['DISTRIB_CODENAME']

    rel = ''
    if src == 'distro':
        try:
            rel = ubuntu_openstack_release[ubuntu_rel]
        except KeyError:
            e = 'Code not derive openstack release for '\
                'this Ubuntu release: %s' % rel
            error_out(e)
        return rel

    if src.startswith('cloud:'):
        ca_rel = src.split(':')[1]
        ca_rel = ca_rel.split('%s-' % ubuntu_rel)[1].split('/')[0]
        return ca_rel

    # Best guess match based on deb string provided
    if src.startswith('deb'):
        for k, v in openstack_codenames.iteritems():
            if v in src:
                return v


def get_os_codename_version(vers):
    '''Determine OpenStack codename from version number.'''
    try:
        return openstack_codenames[vers]
    except KeyError:
        e = 'Could not determine OpenStack codename for version %s' % vers
        error_out(e)


def get_os_version_codename(codename):
    '''Determine OpenStack version number from codename.'''
    for k, v in openstack_codenames.iteritems():
        if v == codename:
            return k
    e = 'Code not derive OpenStack version for '\
        'codename: %s' % codename
    error_out(e)


def get_os_codename_package(pkg):
    '''Derive OpenStack release codename from an installed package.'''
    cmd = ['dpkg', '-l', pkg]

    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        e = 'Could not derive OpenStack version from package that is not '\
            'installed; %s' % pkg
        error_out(e)

    def _clean(line):
        line = line.split(' ')
        clean = []
        for c in line:
            if c != '':
                clean.append(c)
        return clean

    vers = None
    for l in output.split('\n'):
        if l.startswith('ii'):
            l = _clean(l)
            if l[1] == pkg:
                vers = l[2]

    if not vers:
        e = 'Could not determine version of installed package: %s' % pkg
        error_out(e)

    vers = vers[:6]
    try:
        return openstack_codenames[vers]
    except KeyError:
        e = 'Could not determine OpenStack codename for version %s' % vers
        error_out(e)


def configure_installation_source(rel):
    '''Configure apt installation source.'''

    def _import_key(id):
        cmd = "apt-key adv --keyserver keyserver.ubuntu.com " \
              "--recv-keys %s" % id
        try:
            subprocess.check_call(cmd.split(' '))
        except:
            error_out("Error importing repo key %s" % id)

    if rel == 'distro':
        return
    elif rel[:4] == "ppa:":
        src = rel
        subprocess.check_call(["add-apt-repository", "-y", src])
    elif rel[:3] == "deb":
        l = len(rel.split('|'))
        if l == 2:
            src, key = rel.split('|')
            juju_log("Importing PPA key from keyserver for %s" % src)
            _import_key(key)
        elif l == 1:
            src = rel
        else:
            error_out("Invalid openstack-release: %s" % rel)

        with open('/etc/apt/sources.list.d/juju_deb.list', 'w') as f:
            f.write(src)
    elif rel[:6] == 'cloud:':
        ubuntu_rel = lsb_release()['DISTRIB_CODENAME']
        rel = rel.split(':')[1]
        u_rel = rel.split('-')[0]
        ca_rel = rel.split('-')[1]

        if u_rel != ubuntu_rel:
            e = 'Cannot install from Cloud Archive pocket %s on this Ubuntu '\
                'version (%s)' % (ca_rel, ubuntu_rel)
            error_out(e)

        if ca_rel == 'folsom/staging':
            # staging is just a regular PPA.
            cmd = 'add-apt-repository -y '\
                'ppa:ubuntu-cloud-archive/folsom-staging'
            subprocess.check_call(cmd.split(' '))
            return

        # map charm config options to actual archive pockets.
        pockets = {
            'folsom': 'precise-updates/folsom',
            'folsom/updates': 'precise-updates/folsom',
            'folsom/proposed': 'precise-proposed/folsom'
        }

        try:
            pocket = pockets[ca_rel]
        except KeyError:
            e = 'Invalid Cloud Archive release specified: %s' % rel
            error_out(e)

        src = "deb %s %s main" % (CLOUD_ARCHIVE_URL, pocket)
        _import_key(CLOUD_ARCHIVE_KEY_ID)

        with open('/etc/apt/sources.list.d/cloud-archive.list', 'w') as f:
            f.write(src)
    else:
        error_out("Invalid openstack-release specified: %s" % rel)
