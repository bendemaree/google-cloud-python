Using the API
=============

Client
------

:class:`Client <gcloud.dns.client.Client>` objects provide a means to
configure your DNS applications.  Eash instance holds both a ``project``
and an authenticated connection to the DNS service.

For an overview of authentication in ``gcloud-python``, see :doc:`gcloud-auth`.

Assuming your environment is set up as described in that document,
create an instance of :class:`Client <gcloud.dns.client.Client>`.

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client()

Projects
--------

A project is the top-level container in the ``DNS`` API:  it is tied
closely to billing, and can provide default access control across all its
datasets.  If no ``project`` is passed to the client container, the library
attempts to infer a project using the environment (including explicit
environment variables, GAE, or GCE).

To override the project inferred from the environment, pass an explicit
``project`` to the constructor, or to either of the alternative
``classmethod`` factories:

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')

Project Quotas
--------------

Query the quotas for a given project:

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')
     >>> quotas = client.quotas()  # API request
     >>> for key, value in sorted(quotas.items()):
     ...     print('%s: %s' % (key, value))
     managedZones: 10000
     resourceRecordsPerRrset: 100
     rrsetsPerManagedZone: 10000
     rrsetAdditionsPerChange: 100
     rrsetDeletionsPerChange: 100
     totalRrdataSizePerChange: 10000


Project ACLs
~~~~~~~~~~~~

Each project has an access control list granting reader / writer / owner
permission to one or more entities.  This list cannot be queried or set
via the API:  it must be managed using the Google Developer Console.


Managed Zones
-------------

A "managed zone" is the container for DNS records for the same DNS name
suffix and has a set of name servers that accept and responds to queries:

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')
     >>> zone = client.zone('acme-co', description='Acme Company zone',
     ...                    dns_name='example.com')

     >>> zone.exists()  # API request
     False
     >>> zone.create()  # API request
     >>> zone.exists()  # API request
     True

List the zones for a given project:

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')
     >>> zones = client.list_zones()  # API request
     >>> [zone.name for zone in zones]
     ['acme-co']


Resource Record Sets
--------------------

Each managed zone exposes a read-only set of resource records:

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')
     >>> zone = client.zone('acme-co')
     >>> records, page_token = zone.list_resource_record_sets()  # API request
     >>> [(record.name, record.type, record.ttl, record.rrdatas) for record in records]
     [('example.com.', 'SOA', 21600, ['ns-cloud1.googlecomains.com dns-admin.google.com 1 21600 3600 1209600 300'])]

.. note::

   The ``page_token`` returned from ``zone.list_resource_record_sets()`` will
   be an opaque string if there are more resources than can be returned in a
   single request.  To enumerate them all, repeat calling
   ``zone.list_resource_record_sets()``, passing the ``page_token``, until
   the token is ``None``.  E.g.

   .. doctest::

      >>> records, page_token = zone.list_resource_record_sets()  # API request
      >>> while page_token is not None:
      ...     next_batch, page_token = zone.list_resource_record_sets(
      ...         page_token=page_token)  # API request
      ...     records.extend(next_batch)


Change requests
---------------

Update the resource record set for a zone by creating a change request
bundling additions to or deletions from the set.

  .. doctest::

     >>> import time
     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')
     >>> zone = client.zone('acme-co')
     >>> record = dns.ResourceRecord(name='www.example.com', type='CNAME')
     >>> change = zone.change_request(additions=[record])
     >>> change.begin()  # API request
     >>> while change.status != 'done':
     ...     print('Waiting for change to complete')
     ...     time.sleep(60)  # or whatever interval is appropriate
     ...     change.reload()  # API request


List changes made to the resource record set for a given zone:

  .. doctest::

     >>> from gcloud import dns
     >>> client = dns.Client(project='PROJECT_ID')
     >>> zone = client.zone('acme-co')
     >>> changes = []
     >>> changes, page_token = zone.list_changes()  # API request

.. note::

   The ``page_token`` returned from ``zone.list_changes()`` will be
   an opaque string if there are more changes than can be returned in a
   single request.  To enumerate them all, repeat calling
   ``zone.list_changes()``, passing the ``page_token``, until the token
   is ``None``.  E.g.:

   .. doctest::

      >>> changes, page_token = zone.list_changes()  # API request
      >>> while page_token is not None:
      ...     next_batch, page_token = zone.list_changes(
      ...         page_token=page_token)  # API request
      ...     changes.extend(next_batch)
