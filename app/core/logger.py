import logging
import sys
from colorama import Fore, Style, init

# Inicializa o Colorama para funcionar corretamente em sistemas operacionais Unix e Windows
init(autoreset=True)


class CustomFormatter(logging.Formatter):
    """
    Custom logging formatter that applies distinct terminal colors
    based on the severity level of the log message.
    """

    # Formato padrão: [DATA] [NÍVEL] -> MENSAGEM
    log_format = "[%(asctime)s] [%(levelname)s] -> %(message)s"

    FORMATS = {
        logging.DEBUG: Fore.CYAN + log_format + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + log_format + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + log_format + Style.RESET_ALL,
        logging.ERROR: Fore.RED + log_format + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + log_format + Style.RESET_ALL,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Overwrites the default format method to inject custom ANSI colors."""
        log_fmt = self.FORMATS.get(record.levelno, self.log_format)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Factory function to retrieve a configured logger instance with
    the colorful console stream handler attached.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)

    return logger
