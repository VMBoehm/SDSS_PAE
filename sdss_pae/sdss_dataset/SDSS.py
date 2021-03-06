"""SDSS dataset."""

import tensorflow_datasets as tfds
from astropy.io import fits
import json
import tensorflow as tf
import os
import numpy as np

# TODO(SDSS): Markdown description  that will appear on the catalog page.
_DESCRIPTION = """
selected features from spAll and spZbest files 
'flux': measured spectrum in  
'inv_var': inverse variance
'and_mask': and mask (set to 1 for all non-zero entries)
'coeffs': c0, c1, npix. calculate wavelengths with `10.**(c0 + c1 * np.arange(npix))`
'label': type of object, 'STAR'==0, 'QSO'==1, 'GALAXY'==2
'redshift': object redshift estimate
"""

# TODO(SDSS): BibTeX citation
_CITATION = """
"""


class Sdss(tfds.core.GeneratorBasedBuilder):
  """DatasetBuilder for SDSS dataset."""

  VERSION = tfds.core.Version('1.0.0')
  RELEASE_NOTES = {
      '1.0.0': 'Initial release.',
  }

  def _info(self) -> tfds.core.DatasetInfo:
    """Returns the dataset metadata."""
    return tfds.core.DatasetInfo(
        builder=self,
        description=_DESCRIPTION,
        features=tfds.features.FeaturesDict({
            # These are the features of your dataset like images, labels ...
            'flux': tfds.features.Tensor(shape=(None,1),dtype=tf.float32),
            'inv_var': tfds.features.Tensor(shape=(None,1),dtype=tf.float32),
            'and_mask': tfds.features.Tensor(shape=(None,1),dtype=tf.int32),
            'coeffs': tfds.features.Tensor(shape=(3,1), dtype=tf.float32),
            'label': tfds.features.ClassLabel(names=['STAR', 'QSO', 'GALAXY']),
            'redshift': tfds.features.Tensor(shape=(),dtype=tf.float32),
            'filename': tfds.features.Text(),
        }),
        # If there's a common (input, target) tuple from the
        # features, specify them here. They'll be used if
        # `as_supervised=True` in `builder.as_dataset`.
        supervised_keys=None,#('flux'),  # Set to `None` to disable
        homepage='https://www.sdss.org/science/data-release-publications/',
        citation=_CITATION,
    )

  def _split_generators(self, dl_manager: tfds.download.DownloadManager):
    """Returns SplitGenerators."""

    return [
        tfds.core.SplitGenerator(
            name=tfds.Split.TRAIN,
            # These kwargs will be passed to _generate_examples
            gen_kwargs={
            "local_dir": '/global/cscratch1/sd/vboehm/Datasets/SDSS_BOSS_data/',
            "data_dir": '/global/project/projectdirs/cosmo/data/sdss/dr16/sdss/spectro/redux/v5_13_0/'
            },
        ),
    ]

  def _generate_examples(self, local_dir, data_dir):
    """Yields examples."""
    with open(os.path.join(local_dir,'datafiles.txt'), 'r') as infile:
        for line in infile:
            filenames = json.loads(line)
    infile.close()

    with open(os.path.join(local_dir,'z_files.txt'), 'r') as infile:
        for line in infile:
            z_files = json.loads(line)
    infile.close()

    for jj, data_file in enumerate(filenames[0:100]):
        with tf.io.gfile.GFile(os.path.join(data_dir ,z_files[jj]), mode='rb') as f:
            print(data_file)            
            hdulist   = fits.open(f)
            zstruc    = hdulist[1].data
            redshifts = zstruc['z'].astype('float32')
            classes   = zstruc['class']
            f.close()

        with tf.io.gfile.GFile(os.path.join(data_dir ,data_file), mode='rb') as f:
            
            hdulist = fits.open(f)
            flux    = hdulist[0].data.astype('float32')
            ivar_   = hdulist[1].data.astype('float32')
            amask_  = (hdulist[2].data==0).astype('int32')
            
            c0      = hdulist[0].header['coeff0']
            c1      = hdulist[0].header['coeff1']
            npix    = hdulist[0].header['naxis1']
            
            coeffs  = np.expand_dims(np.asarray((c0,c1,npix)),-1).astype('float32') 
            
            for ii in range(1000):
                spec     = np.expand_dims(flux[ii],-1)
                ivar     = np.expand_dims(ivar_[ii],-1)
                amask    = np.expand_dims(amask_[ii],-1)
                redshift = redshifts[ii]
                CLASS    = classes[ii]
                                
                yield '%d'%int(jj*1000+ii), {'filename': data_file, 'flux': spec, 'inv_var': ivar, 'and_mask': amask, 'coeffs': coeffs, 'redshift': redshift, 'label':CLASS}
            f.close()
