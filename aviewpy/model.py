
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import Adams  # type: ignore
from Model import Model  # type: ignore


class Verification():
    """Verification object

    Attributes
    ----------
    verified : bool
        Whether the model was verified
    gruebler : int  
        The gruebler count for the model
    parts : int
        The number of moving parts in the model
    dofs : int
        The number of degrees of freedom in the model
    errors : List[str]  
        List of errors
    messages : List[str]    
        List of messages
    """

    def __init__(self,
                 verified: bool,
                 gruebler: int,
                 parts: int,
                 dofs: int,
                 errors: List[str],
                 messages: List[str]):
        self.verified = verified
        self.messages = messages
        self.gruebler = gruebler
        self.dofs = dofs
        self.errors = errors
        self.parts = parts

    def __bool__(self):
        return self.verified and not self.errors

    @classmethod
    def from_file(cls, file: Path):

        

        verified = False
        messages = []
        errors = []
        gruebler = None
        parts = None
        dofs = None

        text = ''
        for line in file.read_text().splitlines():
            if 'model verified successfully' in line.lower():
                verified = True
            elif line.startswith('VERIFY MODEL:'):
                pass
            elif 'gruebler count' in line.lower():
                gruebler = int(line.split()[0])
            elif 'moving parts' in line.lower():
                parts = int(line.split()[0])
            elif 'degrees of freedom' in line.lower():
                dofs = int(line.split()[0])
            else:
                text += f'{line}\n'

        for line in split_at_double_newline(text):
            if 'ERROR:' in line:
                errors.append(line)
                messages.append(line)
            elif line.strip():
                messages.append(line)

        return cls(verified, gruebler, parts, dofs, errors, messages)

def split_at_double_newline(text: str) -> List[str]:
    """Split text at double newlines

    Parameters
    ----------
    text : str
        Text to split

    Returns
    -------
    List[str]
        List of text blocks
    """
    return [block.replace('\n', ' ') for block in text.split('\n\n') if block.strip()]

def model_verify(mod: Model):
    """Verify a model

    Parameters
    ----------
    mod : Model
        Model to verify

    Returns
    -------
    Verification
        `:class:Verification` object
    """
    with TemporaryDirectory() as tmp_dir:
        file = Path(tmp_dir).resolve() / 'verify.txt'
        Adams.execute_cmd(f'model verify model={mod.full_name} file="{file}" write=off')

        return Verification.from_file(file)
