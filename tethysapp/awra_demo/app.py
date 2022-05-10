from tethys_sdk.base import TethysAppBase, url_map_maker


class AwraDemo(TethysAppBase):
    """
    Tethys app class for AWRA Demo.
    """

    name = 'AWRA Demo'
    description = ''
    package = 'awra_demo'  # WARNING: Do not change this value
    index = 'map'
    icon = f'{package}/images/icon.gif'
    root_url = 'awra-demo'
    color = '#c23616'
    tags = ''
    enable_feedback = False
    feedback_emails = []