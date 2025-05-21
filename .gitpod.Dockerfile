FROM continuumio/miniconda3

# Installa mamba per risolvere più velocemente
RUN conda install -y -n base -c conda-forge mamba

# Crea la cartella workspace
WORKDIR /workspace

# Copia solo i file che esistono, uno per uno (puoi commentarli se non ci sono)
COPY environment.yml /workspace/
COPY requirements.txt /workspace/
COPY wheelhouse/ /workspace/wheelhouse/

# Crea l'env djanalizer solo se environment.yml esiste
RUN test -f /workspace/environment.yml && mamba env create -n djanalizer -f /workspace/environment.yml || echo "⚠️ environment.yml non trovato: skip env creation"

# Auto-attiva l'env in ogni shell
RUN echo "source /opt/conda/etc/profile.d/conda.sh && conda activate djanalizer" >> /etc/profile

# Espone PATH al tuo env
ENV PATH="/opt/conda/envs/djanalizer/bin:${PATH}"