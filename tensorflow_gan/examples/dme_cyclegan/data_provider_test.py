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

import os
import tempfile

from absl import flags
import numpy as np

import tensorflow.compat.v1 as tf

from tensorflow_gan.examples.dme_cyclegan import data_provider
mock = tf.test.mock


class DataProviderTest(tf.test.TestCase):

  def setUp(self):
    super(DataProviderTest, self).setUp()
    self.testdata_dir = os.path.join(
        flags.FLAGS.test_srcdir,
        'tensorflow_gan/examples/dme_cyclegan/testdata')

  def test_normalize_image(self):
    image = tf.random.uniform(shape=(8, 8, 3), maxval=256, dtype=tf.int32)
    rescaled_image = data_provider.normalize_image(image)
    self.assertEqual(tf.float32, rescaled_image.dtype)
    self.assertListEqual(image.shape.as_list(), rescaled_image.shape.as_list())
    with self.cached_session() as sess:
      rescaled_image_out = sess.run(rescaled_image)
      self.assertTrue(np.all(np.abs(rescaled_image_out) <= 1.0))

  def test_sample_patch(self):
    image = tf.zeros(shape=(8, 8, 3))
    patch1 = data_provider._sample_patch(image, 7)
    patch2 = data_provider._sample_patch(image, 10)
    image = tf.zeros(shape=(8, 8, 1))
    patch3 = data_provider._sample_patch(image, 10)
    with self.cached_session() as sess:
      self.assertTupleEqual((7, 7, 3), sess.run(patch1).shape)
      self.assertTupleEqual((10, 10, 3), sess.run(patch2).shape)
      self.assertTupleEqual((10, 10, 3), sess.run(patch3).shape)

  def _test_custom_dataset_provider(self, file_pattern):
    images_ds = data_provider._provide_custom_dataset(file_pattern)
    self.assertEqual(tf.uint8, images_ds.output_types)

    iterator = tf.data.make_initializable_iterator(images_ds)
    with self.cached_session() as sess:
      sess.run(tf.local_variables_initializer())
      sess.run(iterator.initializer)
      images_out_1 = sess.run(iterator.get_next())
      images_out_2 = sess.run(iterator.get_next())
    self.assertEqual(3, images_out_1.shape[-1])
    self.assertEqual(3, images_out_2.shape[-1])

  def test_custom_dataset_provider_file_pattern(self):
    if tf.executing_eagerly():
      # dataset.make_initializable_iterator is not supported when eager
      # execution is enabled.
      return
    file_pattern = os.path.join(self.testdata_dir, '*.jpg')
    self._test_custom_dataset_provider(file_pattern)

  def test_custom_dataset_provider_file_names(self):
    if tf.executing_eagerly():
      # dataset.make_initializable_iterator is not supported when eager
      # execution is enabled.
      return
    file_pattern = os.path.join(self.testdata_dir, '*.jpg')
    file_names = tf.io.gfile.glob(file_pattern)
    file_names_str = '\n'.join(file_names)
    with tempfile.NamedTemporaryFile('w+') as tmp:
      tmp.write(file_names_str)
      tmp.flush()
      self._test_custom_dataset_provider(tmp.name)

  def test_custom_datasets_provider(self):
    if tf.executing_eagerly():
      # dataset.make_initializable_iterator is not supported when eager
      # execution is enabled.
      return
    file_pattern = os.path.join(self.testdata_dir, '*.jpg')
    batch_size = 3
    patch_size = 8
    images_ds_list = data_provider.provide_custom_datasets(
        batch_size=batch_size,
        image_file_patterns=[file_pattern, file_pattern],
        patch_size=patch_size)
    for images_ds in images_ds_list:
      self.assertListEqual([None, patch_size, patch_size, 3],
                           images_ds.output_shapes.as_list())
      self.assertEqual(tf.float32, images_ds.output_types)

    iterators = [tf.data.make_initializable_iterator(x) for x in images_ds_list]
    initialiers = [x.initializer for x in iterators]
    img_tensors = [x.get_next() for x in iterators]
    with self.cached_session() as sess:
      sess.run(tf.local_variables_initializer())
      sess.run(initialiers)
      images_out_list = sess.run(img_tensors)
      for images_out in images_out_list:
        self.assertTupleEqual((batch_size, patch_size, patch_size, 3),
                              images_out.shape)
        self.assertTrue(np.all(np.abs(images_out) <= 1.0))

  def test_custom_data_provider(self):
    if tf.executing_eagerly():
      # dataset.make_initializable_iterator is not supported when eager
      # execution is enabled.
      return
    file_pattern = os.path.join(self.testdata_dir, '*.jpg')
    batch_size = 3
    patch_size = 8
    images_list = data_provider.provide_custom_data(
        batch_size=batch_size,
        image_file_patterns=[file_pattern, file_pattern],
        patch_size=patch_size)
    for images in images_list:
      self.assertListEqual([batch_size, patch_size, patch_size, 3],
                           images.shape.as_list())
      self.assertEqual(tf.float32, images.dtype)

    with self.cached_session() as sess:
      sess.run(tf.local_variables_initializer())
      sess.run(tf.tables_initializer())
      images_out_list = sess.run(images_list)
      for images_out in images_out_list:
        self.assertTupleEqual((batch_size, patch_size, patch_size, 3),
                              images_out.shape)
        self.assertTrue(np.all(np.abs(images_out) <= 1.0))


if __name__ == '__main__':
  tf.test.main()
