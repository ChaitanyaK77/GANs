# coding=utf-8
# Copyright 2023 The TensorFlow GAN Authors.
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

"""Tests for data_provider."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow.compat.v1 as tf

from tensorflow_gan.examples.mnist import data_provider

mock = tf.test.mock


class DataProviderTest(tf.test.TestCase):

  def setUp(self):
    super(DataProviderTest, self).setUp()
    mock_imgs = np.zeros([28, 28, 1], dtype=np.uint8)
    mock_lbls = np.ones([], dtype=np.int64)
    self.mock_ds = tf.data.Dataset.from_tensors({
        'image': mock_imgs,
        'label': mock_lbls
    })

  @mock.patch.object(data_provider, 'tfds', autospec=True)
  def test_provide_dataset(self, mock_tfds):
    batch_size = 5
    mock_tfds.load.return_value = self.mock_ds

    ds = data_provider.provide_dataset('test', batch_size)
    self.assertIsInstance(ds, tf.data.Dataset)

    output = tf.data.get_output_classes(ds)
    self.assertIsInstance(output, dict)
    self.assertSetEqual(set(output.keys()), set(['images', 'labels']))
    self.assertEqual(output['images'], tf.Tensor)
    self.assertEqual(output['labels'], tf.Tensor)

    shapes = tf.data.get_output_shapes(ds)
    self.assertIsInstance(shapes, dict)
    self.assertSetEqual(set(shapes.keys()), set(['images', 'labels']))
    self.assertIsInstance(shapes['images'], tf.TensorShape)
    self.assertIsInstance(shapes['labels'], tf.TensorShape)
    self.assertListEqual(shapes['images'].as_list(), [batch_size, 28, 28, 1])
    self.assertListEqual(shapes['labels'].as_list(), [batch_size, 10])

    types = tf.data.get_output_types(ds)
    self.assertIsInstance(types, dict)
    self.assertSetEqual(set(types.keys()), set(['images', 'labels']))
    self.assertEqual(types['images'], tf.float32)
    self.assertEqual(types['labels'], tf.float32)

    next_batch = tf.data.make_one_shot_iterator(ds).get_next()
    images = next_batch['images']
    labels = next_batch['labels']

    with self.cached_session() as sess:
      images, labels = sess.run([images, labels])

    self.assertEqual(images.shape, (batch_size, 28, 28, 1))
    self.assertTrue(np.all(np.abs(images) <= 1))
    self.assertEqual(labels.shape, (batch_size, 10))

  @mock.patch.object(data_provider, 'tfds', autospec=True)
  def test_provide_data(self, mock_tfds):
    batch_size = 5
    mock_tfds.load.return_value = self.mock_ds

    images, labels = data_provider.provide_data('test', batch_size)

    with self.cached_session() as sess:
      sess.run(tf.tables_initializer())
      images, labels = sess.run([images, labels])
    self.assertTupleEqual(images.shape, (batch_size, 28, 28, 1))
    self.assertTrue(np.all(np.abs(images) <= 1))
    self.assertTupleEqual(labels.shape, (batch_size, 10))

  @mock.patch.object(data_provider, 'tfds', autospec=True)
  def test_provide_data_can_be_reinitialized(self, mock_tfds):
    if tf.executing_eagerly():
      # Trying to access properties or call methods on the result of
      # self.session().
      return
    batch_size = 5
    mock_tfds.load.return_value = self.mock_ds

    images, labels = data_provider.provide_data('test', batch_size)

    with self.session() as sess:
      sess.run([images, labels])
      sess.run([images, labels])
    with self.session() as sess:
      sess.run([images, labels])
      sess.run([images, labels])


if __name__ == '__main__':
  tf.test.main()
