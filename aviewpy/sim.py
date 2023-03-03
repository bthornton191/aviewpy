from numbers import Number
from typing import List, Tuple, Union
from math import log10

def static_funnel(steps: int, **kwargs: Union[float, Tuple[float, float]])->List[str]:
    """Generate a list of acf commands to simulate a static equilibrium funnel.
    
    Parameters
    ----------
    steps : int
        The number of steps in the funnel
    **kwargs : float or Tuple[float, float]]
        The parameters to vary in the funnel. The value can be a single number, in which case
        the parameter is held constant, or a tuple of two numbers, in which case the parameter
        is varied linearly between the two values.
    """
    lines = []
    for step in range(1, steps+1):
        params = []
        for key, value in kwargs.items():
            if isinstance(value, Number):
                val = value
            else:
                start_value, end_value = value

                if start_value > 0 and end_value > 0:

                    # If both values are positive (most likely), interpolate logarithmically
                    start_value = log10(start_value)
                    end_value = log10(end_value)
                    val = 10 ** (start_value + (end_value - start_value) * step / steps)
                
                else:
                    
                    # If either value is negative, interpolate linearly
                    val = start_value + (end_value - start_value) * step / steps
                
            params.append(f'{key}={val:.2e}')
        
        lines.append('equilibrium/' + ', '.join(params))
        lines.append('simulate/static')
    
    return lines
