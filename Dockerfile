FROM continuumio/miniconda:latest

WORKDIR /home/docker_conda_template

COPY ./ ./

RUN chmod +x boot.sh

RUN conda env create -f environment.yml

RUN echo "source activate lp_pyomo" &gt; ~/.bashrc
ENV PATH /opt/conda/envs/lp_pyomo/bin:$PATH

EXPOSE 5000

ENTRYPOINT ["./boot.sh"]