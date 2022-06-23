=======================================
ICEYE InSAR Processor
=======================================
|Language|

.. |Language| image:: https://img.shields.io/badge/python%20-3.7%2B-brightgreen
   :target: .. image:: https://www.python.org/

InSAR processor for Single Look Complex products (SLC) from the ICEYE satellite constellation.

**Installation**:

1. Setup minimal **conda** installation using  `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_
2. Create Python Virtual Environment

    - Creating an environment with commands (`Link <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands>`_);
    - Creating an environment from an environment.yml file (`Link <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file>`_);

3. Install Python Dependencies

    .. code-block:: bash

       conda install -y scipy numpy matplotlib tqdm

4. Install PyGamma - Python module permits a smooth usage of the Gamma Software within Python (`Link <https://gamma-rs.ch/uploads/media/upgrades_info_20210701.pdf>`_);

\
\
**PYTHON DEPENDENCIES**:
 - `py_gamma: Gamma Remote Sensing Python Integration`
 - `numpy: The fundamental package for scientific computing with Python <https://numpy.org>`_
