from src.autoscaler import AutoScaler

def test_high_traffic_triggers_scale_up(mocker):
    """
    Test the AutoScaler scales UP when traffic exceeds the high threshold (2.0)
    """
    mocker.patch('src.autoscaler.DatabaseManager')
    mocker.patch('src.autoscaler.Actuator')

    scaler = AutoScaler()

    scaler.db.get_config.return_value = "auto"
    scaler.db.get_recent_metrics.return_value = [{'network': 3.5}]
    scaler.decide()

    scaler.actuator.scale_up.assert_called_once()
    scaler.actuator.scale_down.assert_not_called()

def test_low_traffic_triggers_scale_down(mocker):
    """
    Test the AutoScaler sclaes DOWN when traffic drops below the low threshold (0.1)
    """
    mocker.patch('src.autoscaler.DatabaseManager')
    mocker.patch('src.autoscaler.Actuator')

    scaler = AutoScaler()

    scaler.db.get_config.return_value = "auto"
    scaler.db.get_recent_metrics.return_value = [{'network': 0.05}]
    scaler.decide()

    scaler.actuator.scale_down.assert_called_once()
    scaler.actuator.scale_up.assert_not_called()

def test_manual_mode_pauses_autoscaler(mocker):
    """
    Test the AutoScaler does nothing if the database says 'manual'
    """
    mocker.patch('src.autoscaler.DatabaseManager')
    mocker.patch('src.autoscaler.Actuator')

    scaler = AutoScaler()

    scaler.db.get_config.return_value = "manual"
    scaler.decide()

    scaler.db.get_recent_metrics.assert_not_called()
    scaler.actuator.scale_up.assert_not_called()
    scaler.actuator.scale_down.assert_not_called()