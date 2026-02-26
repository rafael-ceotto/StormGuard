"""
CNN-LSTM Hybrid Model
======================
Combines Convolutional Neural Networks for spatial feature extraction
with LSTM for temporal pattern recognition.

Architecture:
- Input 1: Spatial (Satellite images or weather maps) → CNN
- Input 2: Temporal (Weather time series) → LSTM
- Fusion: Concatenate CNN output with LSTM output
- Dense layers → Binary classification
"""

import tensorflow as tf
from tensorflow.keras import layers, Model
import logging

logger = logging.getLogger(__name__)

class CNNLSTMModel:
    """CNN-LSTM hybrid model"""
    
    def __init__(self, config: dict = None):
        """
        Initialize model
        
        Args:
            config: Model configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.model = self._build_model()
    
    @staticmethod
    def _get_default_config() -> dict:
        """Get default model configuration"""
        return {
            'spatial_shape': (64, 64, 3),  # Weather map: 64x64 RGB
            'temporal_steps': 30,  # 30 hours
            'temporal_features': 10,  # Temperature, humidity, pressure, etc
            'cnn_filters': [32, 64, 128],
            'cnn_kernel_size': 3,
            'lstm_units': 128,
            'dense_units': [256, 128],
            'dropout_rate': 0.3,
            'activation': 'relu',
        }
    
    def _build_model(self) -> Model:
        """
        Build the hybrid CNN-LSTM model
        """
        logger.info("Building CNN-LSTM model")
        
        cfg = self.config
        
        # ===== SPATIAL PATHWAY (CNN) =====
        spatial_input = layers.Input(
            shape=cfg['spatial_shape'],
            name='spatial_input'  # Weather maps/satellite images
        )
        
        x = spatial_input
        
        # CNN blocks
        for filters in cfg['cnn_filters']:
            x = layers.Conv2D(
                filters=filters,
                kernel_size=cfg['cnn_kernel_size'],
                activation=cfg['activation'],
                padding='same'
            )(x)
            x = layers.MaxPooling2D(pool_size=2)(x)
            x = layers.BatchNormalization()(x)
        
        # Flatten for concatenation
        spatial_features = layers.Flatten()(x)
        spatial_features = layers.Dense(256, activation=cfg['activation'])(spatial_features)
        spatial_features = layers.Dropout(cfg['dropout_rate'])(spatial_features)
        
        # ===== TEMPORAL PATHWAY (LSTM) =====
        temporal_input = layers.Input(
            shape=(cfg['temporal_steps'], cfg['temporal_features']),
            name='temporal_input'  # Weather time series
        )
        
        y = temporal_input
        
        # LSTM layers
        y = layers.LSTM(
            units=cfg['lstm_units'],
            return_sequences=True,
            dropout=cfg['dropout_rate']
        )(y)
        
        y = layers.LSTM(
            units=cfg['lstm_units'],
            return_sequences=False,
            dropout=cfg['dropout_rate']
        )(y)
        
        y = layers.Dense(256, activation=cfg['activation'])(y)
        y = layers.Dropout(cfg['dropout_rate'])(y)
        
        # ===== FUSION =====
        fusion = layers.Concatenate()([spatial_features, y])
        
        fusion = layers.Dense(cfg['dense_units'][0], activation=cfg['activation'])(fusion)
        fusion = layers.BatchNormalization()(fusion)
        fusion = layers.Dropout(cfg['dropout_rate'])(fusion)
        
        fusion = layers.Dense(cfg['dense_units'][1], activation=cfg['activation'])(fusion)
        fusion = layers.Dropout(cfg['dropout_rate'])(fusion)
        
        # ===== OUTPUT =====
        output = layers.Dense(1, activation='sigmoid', name='disaster_probability')(fusion)
        
        # Build model
        model = Model(
            inputs=[spatial_input, temporal_input],
            outputs=output,
            name='CNN_LSTM_Disaster_Predictor'
        )
        
        logger.info(f"Model built with {model.count_params()} parameters")
        
        return model
    
    def compile_model(self, learning_rate: float = 0.001):
        """Compile model with optimizer and loss"""
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        
        self.model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=[
                tf.keras.metrics.AUC(name='auc'),
                tf.keras.metrics.Precision(name='precision'),
                tf.keras.metrics.Recall(name='recall'),
            ]
        )
        
        logger.info("Model compiled")
    
    def get_model(self) -> Model:
        """Return the Keras model"""
        return self.model
    
    def summary(self):
        """Print model summary"""
        return self.model.summary()
