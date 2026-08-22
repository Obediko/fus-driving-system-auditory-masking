# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Margely Cornelissen, Stein Fekkes (Radboud University) and Erik Dumont (Image
Guided Therapy)

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

**Attribution Notice**:
If you use this kit in your research or project, please refer to the 'How to Cite' section in the
README.md file of https://github.com/Donders-Institute/Radboud-FUS-driving-system-software.

Integrated Dortmund auditory-masking adaptation:
Apochi, O., & Axmacher, N. (2026). Focused Ultrasound Driving System with
Synchronized Auditory Masking for Active and Sham Entorhinal Cortex Stimulation
(Version 1.0.0) [Computer software]. Zenodo.
https://doi.org/10.5281/zenodo.22059704
"""

from setuptools import setup, find_packages

setup(name='fus_driving_systems',
      version='2.2.3',
      description='Focused-ultrasound driving systems with synchronized research-only auditory masking',
      url='https://github.com/Obediko/fus-driving-system-auditory-masking',
      author='Margely Cornelissen',
      author_email='margely.cornelissen@ru.nl',
      maintainer='Apochi Obed and Nikolai Axmacher',
      project_urls={
          'Published adaptation DOI': 'https://doi.org/10.5281/zenodo.22059704',
          'Zenodo software record': 'https://zenodo.org/records/22059704',
          'Adaptation source': 'https://github.com/Obediko/fus-driving-system-auditory-masking',
          'Upstream Radboud driver': 'https://github.com/Donders-Institute/Radboud-FUS-driving-system-software',
          'Upstream auditory masking DOI': 'https://doi.org/10.5281/zenodo.20681923',
      },
      packages=find_packages(),
      package_data={'fus_driving_systems': ['config/*', 'igt/config/imasonic_transducers/*',
                                            'igt/config/sonic_concepts_transducers/*',
                                            'igt/config/conversion_data/*',
                                            'igt/config/*.json', 'igt/*.pyd',
                                            'auditory_masking/_vendor/LICENSE',
                                            'auditory_masking/_vendor/EULA.md',
                                            'auditory_masking/_vendor/NOTICE.md']},
      py_modules=['driving_system', 'transducer', 'control_driving_system', 'sequence', 'utils'],
      zip_safe=False)
