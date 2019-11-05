import os
import pickle

import numpy as np
import torch

from pytorch_lightning import Trainer
from pytorch_lightning.testing import LightningTestModel
from pytorch_lightning.logging import LightningLoggerBase, rank_zero_only
from . import testing_utils

RANDOM_FILE_PATHS = list(np.random.randint(12000, 19000, 1000))
ROOT_SEED = 1234
torch.manual_seed(ROOT_SEED)
np.random.seed(ROOT_SEED)
RANDOM_SEEDS = list(np.random.randint(0, 10000, 1000))


def test_testtube_logger():
    """
    verify that basic functionality of test tube logger works
    """
    reset_seed()
    hparams = testing_utils.get_hparams()
    model = LightningTestModel(hparams)

    save_dir = testing_utils.init_save_dir()

    logger = testing_utils.get_test_tube_logger(False)

    trainer_options = dict(
        max_nb_epochs=1,
        train_percent_check=0.01,
        logger=logger
    )

    trainer = Trainer(**trainer_options)
    result = trainer.fit(model)

    assert result == 1, "Training failed"

    testing_utils.clear_save_dir()


def test_testtube_pickle():
    """
    Verify that pickling a trainer containing a test tube logger works
    """
    reset_seed()

    hparams = testing_utils.get_hparams()
    model = LightningTestModel(hparams)

    save_dir = testing_utils.init_save_dir()

    logger = testing_utils.get_test_tube_logger(False)
    logger.log_hyperparams(hparams)
    logger.save()

    trainer_options = dict(
        max_nb_epochs=1,
        train_percent_check=0.01,
        logger=logger
    )

    trainer = Trainer(**trainer_options)
    pkl_bytes = pickle.dumps(trainer)
    trainer2 = pickle.loads(pkl_bytes)
    trainer2.logger.log_metrics({"acc": 1.0})

    testing_utils.clear_save_dir()


def test_mlflow_logger():
    """
    verify that basic functionality of mlflow logger works
    """
    reset_seed()

    try:
        from pytorch_lightning.logging import MLFlowLogger
    except ModuleNotFoundError:
        return

    hparams = testing_utils.get_hparams()
    model = LightningTestModel(hparams)

    root_dir = os.path.dirname(os.path.realpath(__file__))
    mlflow_dir = os.path.join(root_dir, "mlruns")

    logger = MLFlowLogger("test", f"file://{mlflow_dir}")

    trainer_options = dict(
        max_nb_epochs=1,
        train_percent_check=0.01,
        logger=logger
    )

    trainer = Trainer(**trainer_options)
    result = trainer.fit(model)

    print('result finished')
    assert result == 1, "Training failed"

    testing_utils.clear_save_dir()


def test_mlflow_pickle():
    """
    verify that pickling trainer with mlflow logger works
    """
    reset_seed()

    try:
        from pytorch_lightning.logging import MLFlowLogger
    except ModuleNotFoundError:
        return

    hparams = testing_utils.get_hparams()
    model = LightningTestModel(hparams)

    root_dir = os.path.dirname(os.path.realpath(__file__))
    mlflow_dir = os.path.join(root_dir, "mlruns")

    logger = MLFlowLogger("test", f"file://{mlflow_dir}")

    trainer_options = dict(
        max_nb_epochs=1,
        logger=logger
    )

    trainer = Trainer(**trainer_options)
    pkl_bytes = pickle.dumps(trainer)
    trainer2 = pickle.loads(pkl_bytes)
    trainer2.logger.log_metrics({"acc": 1.0})

    testing_utils.clear_save_dir()


def test_custom_logger(tmpdir):

    class CustomLogger(LightningLoggerBase):
        def __init__(self):
            super().__init__()
            self.hparams_logged = None
            self.metrics_logged = None
            self.finalized = False

        @rank_zero_only
        def log_hyperparams(self, params):
            self.hparams_logged = params

        @rank_zero_only
        def log_metrics(self, metrics, step_num):
            self.metrics_logged = metrics

        @rank_zero_only
        def finalize(self, status):
            self.finalized_status = status

        @property
        def name(self):
            return "name"

        @property
        def version(self):
            return "1"

    hparams = testing_utils.get_hparams()
    model = LightningTestModel(hparams)

    logger = CustomLogger()

    trainer_options = dict(
        max_nb_epochs=1,
        train_percent_check=0.01,
        logger=logger,
        default_save_path=tmpdir
    )

    trainer = Trainer(**trainer_options)
    result = trainer.fit(model)
    assert result == 1, "Training failed"
    assert logger.hparams_logged == hparams
    assert logger.metrics_logged != {}
    assert logger.finalized_status == "success"


def reset_seed():
    SEED = RANDOM_SEEDS.pop()
    torch.manual_seed(SEED)
    np.random.seed(SEED)
