FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    grep \
    coreutils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Configure conda channels and create environment with bio tools including HMMER
RUN conda config --add channels defaults \
    && conda config --add channels conda-forge \
    && conda config --add channels bioconda

# Install mamba (faster and more reliable solver) then create the env with mamba
RUN conda install -n base -c conda-forge mamba -y && \
    mamba create -n bio -y \
    python=3.10 \
    blast \
    bwa \
    samtools \
    bowtie2 \
    hisat2 \
    salmon \
    kallisto \
    fastqc \
    cutadapt \
    hmmer \
    && conda clean -afy

# Ensure the conda 'bio' environment binaries are on PATH at runtime so
# commands like 'hmmfetch' are available without explicit activation.
ENV PATH="/opt/conda/envs/bio/bin:${PATH}"

SHELL ["conda", "run", "-n", "bio", "/bin/bash", "-c"]

WORKDIR /workspace

# Create symlinks for key HMMER binaries into /usr/local/bin so they are
# always available regardless of shell PATH handling in different runtimes.
RUN ln -s /opt/conda/envs/bio/bin/hmmfetch /usr/local/bin/hmmfetch || true && \
    ln -s /opt/conda/envs/bio/bin/hmmpress /usr/local/bin/hmmpress || true && \
    ln -s /opt/conda/envs/bio/bin/hmmsearch /usr/local/bin/hmmsearch || true && \
    ln -s /opt/conda/envs/bio/bin/hmmscan /usr/local/bin/hmmscan || true

CMD [ "bash" ] 
