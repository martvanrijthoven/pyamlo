"""Test the new !@$ interpolated call syntax."""
import pytest
from pyamlo.tags import ConfigLoader, CallSpec
from pyamlo.resolve import Resolver
import yaml


def test_interpolated_callspec_basic():
    """Test basic !@ syntax with $variable interpolation."""
    yaml_content = """
    counter_type: "Counter"
    word_count: !@collections.$counter_type
      - ["apple", "banana", "apple", "cherry"]
    """
    
    data = yaml.load(yaml_content, Loader=ConfigLoader)
    assert isinstance(data['word_count'], CallSpec)
    assert data['word_count'].is_interpolated == True
    assert data['word_count'].path == "collections.$counter_type"
    
    resolver = Resolver()
    resolved = resolver.resolve(data)
    
    # Should create a collections.Counter
    counter = resolved['word_count']
    assert str(type(counter)) == "<class 'collections.Counter'>"
    assert counter['apple'] == 2
    assert counter['banana'] == 1
    assert counter['cherry'] == 1


def test_interpolated_callspec_variable_only():
    """Test !@ syntax where variable is the entire path."""
    yaml_content = """
    target_class: "collections.deque"
    container: !@$target_class
      maxlen: 5
    """
    
    data = yaml.load(yaml_content, Loader=ConfigLoader)
    assert isinstance(data['container'], CallSpec)
    assert data['container'].is_interpolated == True
    assert data['container'].path == "$target_class"
    
    resolver = Resolver()
    resolved = resolver.resolve(data)
    
    container = resolved['container']
    assert str(type(container)) == "<class 'collections.deque'>"
    assert container.maxlen == 5


def test_interpolated_callspec_with_args():
    """Test !@ syntax with positional arguments."""
    yaml_content = """
    dict_type: "OrderedDict"
    ordered_dict: !@collections.$dict_type
      key1: "value1"
      key2: "value2"
    """
    
    data = yaml.load(yaml_content, Loader=ConfigLoader)
    resolver = Resolver()
    resolved = resolver.resolve(data)
    
    ordered_dict = resolved['ordered_dict']
    assert str(type(ordered_dict)) == "<class 'collections.OrderedDict'>"
    assert list(ordered_dict.keys()) == ["key1", "key2"]
    assert list(ordered_dict.values()) == ["value1", "value2"]


def test_interpolated_callspec_multiple_variables():
    """Test multiple !@ tags with $ interpolation in same config."""
    yaml_content = """
    container_type: "deque"
    counter_type: "Counter"
    
    containers:
      queue: !@collections.$container_type
        maxlen: 100
      word_count: !@collections.$counter_type
        - ["word1", "word2", "word1"]
      another_queue: !@collections.$container_type
        maxlen: 50
    """
    
    data = yaml.load(yaml_content, Loader=ConfigLoader)
    resolver = Resolver()
    resolved = resolver.resolve(data)
    
    containers = resolved['containers']
    assert str(type(containers['queue'])) == "<class 'collections.deque'>"
    assert containers['queue'].maxlen == 100
    assert str(type(containers['word_count'])) == "<class 'collections.Counter'>"
    assert containers['word_count']['word1'] == 2
    assert containers['another_queue'].maxlen == 50


def test_interpolated_callspec_multiple_dollar_signs():
    """Test multiple $ interpolations in a single path."""
    yaml_content = """
    module_name: "collections"
    class_name: "Counter"
    my_counter: !@$module_name.$class_name
      - ["apple", "banana", "apple", "cherry"]
    
    base_module: "collections"
    sub_class: "OrderedDict"
    my_dict: !@$base_module.$sub_class
      key1: "value1"
      key2: "value2"
    """
    
    data = yaml.load(yaml_content, Loader=ConfigLoader)
    resolver = Resolver()
    resolved = resolver.resolve(data)
    
    # Test the Counter
    counter = resolved['my_counter']
    assert str(type(counter)) == "<class 'collections.Counter'>"
    assert counter['apple'] == 2
    assert counter['banana'] == 1
    assert counter['cherry'] == 1
    
    # Test the OrderedDict
    my_dict = resolved['my_dict']
    assert str(type(my_dict)) == "<class 'collections.OrderedDict'>"
    assert list(my_dict.keys()) == ["key1", "key2"]
    assert list(my_dict.values()) == ["value1", "value2"]


def test_interpolated_callspec_error_handling():
    """Test error handling for undefined variables."""
    yaml_content = """
    model: !@torch.nn.$undefined_var
      in_features: 10
      out_features: 5
    """
    
    data = yaml.load(yaml_content, Loader=ConfigLoader)
    resolver = Resolver()
    
    with pytest.raises(Exception):  # Should raise ResolutionError for undefined variable
        resolver.resolve(data)
