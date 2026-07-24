# MAVEN User Guide
Diana Maven is a local host interface designed to automate the collection of metadata for DIANA datasets using URSA. 
It streamlines the process of gathering necessary dataset information before moving data and metadata to a specified HPC campaign directory via DSI.

## Quick Start

If already installed, simply run: `diana` in your terminal.
Then, open the provided localhost URL in your preferred browser.


## Installation and Setup

### Prerequisites
- Python 3.12+

### Virtual Environment
It is recommended users create a virtual environment to run MAVEN with Python 3.12+. 

**Option A: Miniconda3**
```
. ~/miniconda3/bin/activate
conda create -n diana_env python=3.12
conda activate diana_env                # start here if virtual environment exists
```
**Option B: Python venv**
```
python3 -m venv diana_env
source diana_env/bin/activate           # start here if virtual environment exists
pip install --upgrade pip
```
**Option C: uv**
```
uv venv
source .venv/bin/activate
```

### Installation
Install the project and its dependencies using pip: `pip install .`

### Setup
When first launching the app, you will be prompted to complete 3 fields:
1) **Diana Maven Directory**: Where your metadata databases will be locally saved.
2) **AI API Key**: Secret API key to connect to an AI model with [URSA](https://github.com/lanl/ursa)
3) **AI Base URL**: Endpoint to connect to an AI model


For further instructions on setting up an AI API Key, please contact a MAVEN team member.

### HPC & DSI Setup
To move data to an HPC campaign space using [DSI](https://github.com/lanl/dsi), contact a MAVEN team member for setup details.

## App Notes
The app collects 3 levels of metadata:

### 1. The Genesis Datasheet (Sections 1-8)
These sections follow the Genesis Datasheet format. URSA leverages your **Project Description** and **Clarification** responses to autofill these fields. 

### 2. Findability Metadata
High-level metadata used for indexing and searching.

### 3. AI-Ready Metadata
Domain-specific technical metadata that extracts values and types from the data.

Once all levels are complete, the app enables users to move data and metadata to the chosen HPC campaign directory.


# Copyright and License

This program is Open-Source under the BSD-3 License.

© 2026. Triad National Security, LLC. All rights reserved. **O5152**

This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.


Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.