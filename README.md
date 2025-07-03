# PyDownloader Moderno

Um downloader de vídeos do YouTube com uma interface gráfica moderna, construído em Python com PySide6 e yt-dlp.

![Screenshot do Programa](URL_DA_SUA_IMAGEM_AQUI)
_Você pode tirar um print da sua aplicação e subir em um site como o [Imgur](https://imgur.com/upload) para gerar a URL da imagem._

## Funcionalidades

- Interface gráfica responsiva que não congela durante as operações.
- Análise de vídeos para exibir título e qualidade disponível.
- Download de vídeos do YouTube (longos, lives gravadas e Shorts).
- Usa o FFmpeg para juntar áudio e vídeo, garantindo a melhor qualidade.
- Exibe o progresso do download e mensagens de status claras.

## Pré-requisitos

Para que a fusão de áudio e vídeo funcione, você **precisa ter o FFmpeg instalado** e acessível no PATH do seu sistema.

1.  **Baixe o FFmpeg:** Você pode obter os arquivos no site oficial: [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) (recomenda-se a versão `essentials`).
2.  **Instale e adicione ao PATH:** Siga um guia para adicionar a pasta `bin` do FFmpeg às variáveis de ambiente do seu sistema operacional.
3.  **Verifique:** Abra um **novo** terminal e digite `ffmpeg -version`. Se aparecerem informações da versão, está tudo certo.

## Instalação do Projeto

1.  **Clone o repositório:**

    ```bash
    git clone [https://github.com/S-carLord/Video_Downloader](https://github.com/S-carLord/Video_Downloader)
    cd Video_Downloader
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    # Cria o ambiente
    python -m venv .venv
    # Ativa o ambiente (Windows)
    .venv\Scripts\activate
    # Ativa o ambiente (macOS/Linux)
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Como Usar

Com o ambiente virtual ativado, execute o programa:

```bash
python Video_Downloader.py
```

Cole a URL de um vídeo, clique em "Analisar" e, em seguida, em "Baixar". Os vídeos serão salvos em uma subpasta chamada `Downloads`.
