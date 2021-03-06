# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest2


class Test__get_cluster(unittest2.TestCase):

    def _callFUT(self, timeout=None):
        from gcloud.bigtable.happybase.connection import _get_cluster
        return _get_cluster(timeout=timeout)

    def _helper(self, timeout=None, clusters=(), failed_zones=()):
        from functools import partial
        from gcloud._testing import _Monkey
        from gcloud.bigtable.happybase import connection as MUT

        client_with_clusters = partial(_Client, clusters=clusters,
                                       failed_zones=failed_zones)
        with _Monkey(MUT, Client=client_with_clusters):
            result = self._callFUT(timeout=timeout)

        # If we've reached this point, then _callFUT didn't fail, so we know
        # there is exactly one cluster.
        cluster, = clusters
        self.assertEqual(result, cluster)
        client = cluster.client
        self.assertEqual(client.args, ())
        expected_kwargs = {'admin': True}
        if timeout is not None:
            expected_kwargs['timeout_seconds'] = timeout / 1000.0
        self.assertEqual(client.kwargs, expected_kwargs)
        self.assertEqual(client.start_calls, 1)
        self.assertEqual(client.stop_calls, 1)

    def test_default(self):
        cluster = _Cluster()
        self._helper(clusters=[cluster])

    def test_with_timeout(self):
        cluster = _Cluster()
        self._helper(timeout=2103, clusters=[cluster])

    def test_with_no_clusters(self):
        with self.assertRaises(ValueError):
            self._helper()

    def test_with_too_many_clusters(self):
        clusters = [_Cluster(), _Cluster()]
        with self.assertRaises(ValueError):
            self._helper(clusters=clusters)

    def test_with_failed_zones(self):
        cluster = _Cluster()
        failed_zone = 'us-central1-c'
        with self.assertRaises(ValueError):
            self._helper(clusters=[cluster],
                         failed_zones=[failed_zone])


class TestConnection(unittest2.TestCase):

    def _getTargetClass(self):
        from gcloud.bigtable.happybase.connection import Connection
        return Connection

    def _makeOne(self, *args, **kwargs):
        return self._getTargetClass()(*args, **kwargs)

    def test_constructor_defaults(self):
        cluster = _Cluster()  # Avoid implicit environ check.
        self.assertEqual(cluster._client.start_calls, 0)
        connection = self._makeOne(cluster=cluster)
        self.assertEqual(cluster._client.start_calls, 1)
        self.assertEqual(cluster._client.stop_calls, 0)

        self.assertEqual(connection._cluster, cluster)
        self.assertEqual(connection.table_prefix, None)
        self.assertEqual(connection.table_prefix_separator, '_')

    def test_constructor_no_autoconnect(self):
        cluster = _Cluster()  # Avoid implicit environ check.
        connection = self._makeOne(autoconnect=False, cluster=cluster)
        self.assertEqual(cluster._client.start_calls, 0)
        self.assertEqual(cluster._client.stop_calls, 0)
        self.assertEqual(connection.table_prefix, None)
        self.assertEqual(connection.table_prefix_separator, '_')

    def test_constructor_missing_cluster(self):
        from gcloud._testing import _Monkey
        from gcloud.bigtable.happybase import connection as MUT

        cluster = _Cluster()
        timeout = object()
        get_cluster_called = []

        def mock_get_cluster(timeout):
            get_cluster_called.append(timeout)
            return cluster

        with _Monkey(MUT, _get_cluster=mock_get_cluster):
            connection = self._makeOne(autoconnect=False, cluster=None,
                                       timeout=timeout)
            self.assertEqual(connection.table_prefix, None)
            self.assertEqual(connection.table_prefix_separator, '_')
            self.assertEqual(connection._cluster, cluster)

        self.assertEqual(get_cluster_called, [timeout])

    def test_constructor_explicit(self):
        autoconnect = False
        table_prefix = 'table-prefix'
        table_prefix_separator = 'sep'
        cluster_copy = _Cluster()
        cluster = _Cluster(copies=[cluster_copy])

        connection = self._makeOne(
            autoconnect=autoconnect,
            table_prefix=table_prefix,
            table_prefix_separator=table_prefix_separator,
            cluster=cluster)
        self.assertEqual(connection.table_prefix, table_prefix)
        self.assertEqual(connection.table_prefix_separator,
                         table_prefix_separator)

    def test_constructor_with_unknown_argument(self):
        cluster = _Cluster()
        with self.assertRaises(TypeError):
            self._makeOne(cluster=cluster, unknown='foo')

    def test_constructor_with_legacy_args(self):
        from gcloud._testing import _Monkey
        from gcloud.bigtable.happybase import connection as MUT

        warned = []

        def mock_warn(msg):
            warned.append(msg)

        cluster = _Cluster()
        with _Monkey(MUT, _WARN=mock_warn):
            self._makeOne(cluster=cluster, host=object(),
                          port=object(), compat=object(),
                          transport=object(), protocol=object())

        self.assertEqual(len(warned), 1)
        self.assertIn('host', warned[0])
        self.assertIn('port', warned[0])
        self.assertIn('compat', warned[0])
        self.assertIn('transport', warned[0])
        self.assertIn('protocol', warned[0])

    def test_constructor_with_timeout_and_cluster(self):
        cluster = _Cluster()
        with self.assertRaises(ValueError):
            self._makeOne(cluster=cluster, timeout=object())

    def test_constructor_non_string_prefix(self):
        table_prefix = object()

        with self.assertRaises(TypeError):
            self._makeOne(autoconnect=False,
                          table_prefix=table_prefix)

    def test_constructor_non_string_prefix_separator(self):
        table_prefix_separator = object()

        with self.assertRaises(TypeError):
            self._makeOne(autoconnect=False,
                          table_prefix_separator=table_prefix_separator)

    def test_open(self):
        cluster = _Cluster()  # Avoid implicit environ check.
        connection = self._makeOne(autoconnect=False, cluster=cluster)
        self.assertEqual(cluster._client.start_calls, 0)
        connection.open()
        self.assertEqual(cluster._client.start_calls, 1)
        self.assertEqual(cluster._client.stop_calls, 0)

    def test_close(self):
        cluster = _Cluster()  # Avoid implicit environ check.
        connection = self._makeOne(autoconnect=False, cluster=cluster)
        self.assertEqual(cluster._client.stop_calls, 0)
        connection.close()
        self.assertEqual(cluster._client.stop_calls, 1)
        self.assertEqual(cluster._client.start_calls, 0)

    def test___del__with_cluster(self):
        cluster = _Cluster()  # Avoid implicit environ check.
        connection = self._makeOne(autoconnect=False, cluster=cluster)
        self.assertEqual(cluster._client.stop_calls, 0)
        connection.__del__()
        self.assertEqual(cluster._client.stop_calls, 1)

    def test___del__no_cluster(self):
        cluster = _Cluster()  # Avoid implicit environ check.
        connection = self._makeOne(autoconnect=False, cluster=cluster)
        self.assertEqual(cluster._client.stop_calls, 0)
        del connection._cluster
        connection.__del__()
        self.assertEqual(cluster._client.stop_calls, 0)


class _Client(object):

    def __init__(self, *args, **kwargs):
        self.clusters = kwargs.pop('clusters', [])
        for cluster in self.clusters:
            cluster.client = self
        self.failed_zones = kwargs.pop('failed_zones', [])
        self.args = args
        self.kwargs = kwargs
        self.start_calls = 0
        self.stop_calls = 0

    def start(self):
        self.start_calls += 1

    def stop(self):
        self.stop_calls += 1

    def list_clusters(self):
        return self.clusters, self.failed_zones


class _Cluster(object):

    def __init__(self, copies=(), list_tables_result=()):
        self.copies = list(copies)
        # Included to support Connection.__del__
        self._client = _Client()
        self.list_tables_result = list_tables_result

    def copy(self):
        if self.copies:
            result = self.copies[0]
            self.copies[:] = self.copies[1:]
            return result
        else:
            return self
