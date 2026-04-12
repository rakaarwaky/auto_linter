from agent.dependency_injection_container import Container, get_container
from agent import dependency_injection_container as container_mod

def test_container_init():
    container = Container()
    assert len(container.adapters) == 11
    assert container.venv_bin is not None
    assert container.analysis_use_case is not None
    assert container.fixes_use_case is not None

def test_get_container_singleton():
    # Reset singleton for testing
    container_mod._container = None
    
    c1 = get_container()
    c2 = get_container()
    
    assert c1 is c2
    assert isinstance(c1, Container)
