FROM continuumio/miniconda3

# installa mamba per risolvere più velocemente
RUN conda install -y -n base -c conda-forge mamba

# copia i file di definizione
COPY environment.yml requirements.txt wheelhouse/ /workspace/

# crea l'env djanalizer
RUN mamba env create -n djanalizer -f /workspace/environment.yml

# auto-attiva l'env in ogni shell
RUN echo "source /opt/conda/etc/profile.d/conda.sh && conda activate djanalizer" >> /etc/profile

# espone PATH al tuo env
ENV PATH="/opt/conda/envs/djanalizer/bin:${PATH}"
