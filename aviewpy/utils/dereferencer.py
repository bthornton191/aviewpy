from collections import namedtuple
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import List

import Adams  # type: ignore # noqa
from aviewpy.objects import delete_objects, get_managers, get_object
from aviewpy.objects import get_parent_model
from aviewpy.ui.alerts import adams_errors_suppressed

from DBAccess import SetValueFailed  # type: ignore # noqa
from Model import Model  # type: ignore # noqa
from Object import Object  # type: ignore # noqa

Property = namedtuple('Property', ['entity', 'name', 'value'])


class Dereferencer():
    def __init__(self, entity: Object):
        self.entity = entity
        self.dep_props: List[Property] = []
        self.mod: Model = get_parent_model(self.entity)
        self.entity_copy: Object = None
        self.files: List[Path] = []
        self.export_dir: Path = None

    def dereference(self):
        """Removes all references to `self.entity`

        Note
        ----
        Only removes references from **direct** children of the model.
        """
        self.entity_copy = self.entity.copy()
        for manager in get_managers(self.mod):
            for ent in manager.values():
                ent: Object = ent
                for prop_name in ent.properties:
                    try:
                        prop_val = getattr(ent, prop_name)
                    except AttributeError:
                        continue
                    
                    if isinstance(prop_val, Object) and prop_val == self.entity:

                        # If the property is a **sigleton**

                        # Store Original
                        self.dep_props.append(Property(ent, prop_name, prop_val.full_name))

                        # Remove referece
                        with adams_errors_suppressed():
                            try:
                                setattr(ent, prop_name, self.entity_copy)
                            except SetValueFailed:
                                pass

                    elif (isinstance(prop_val, List) and self.entity in prop_val):
                        
                        # If the property is a **list**
                        prop_val: List[Object] = prop_val

                        # Store Original
                        self.dep_props.append(Property(ent,
                                                       prop_name,
                                                       [obj.full_name for obj in prop_val]))

                        # Remove referece
                        with adams_errors_suppressed():
                            try:
                                setattr(ent, prop_name, [v for v in prop_val if v != self.entity] or [self.entity_copy])
                            except SetValueFailed:
                                pass
        
        # Check for dependent contact incidents
        if Adams.evaluate_exp(f'db_object_count(DB_DEPENDENTS({self.entity.full_name}, "incident"))') > 0:
            self._write_all_contact_incidents()

    def _write_all_contact_incidents(self):
        """Write analyses to files and delete from database
        """
        self.export_dir = Path(mkdtemp())
        inc_names = Adams.evaluate_exp(f'DB_DEPENDENTS({self.entity.full_name}, "incident")')
        ans_names = [Adams.evaluate_exp(f'DB_ANCESTOR({inc_name}, "Analysis")')
                     for inc_name in inc_names]
                     
        for ans_name in set(ans_names):
            ans = self.mod.Analyses[ans_name.split('.')[-1]]

            if False:
                incident_container = f'{ans.full_name}.CONTACT_INCIDENTS'
                file = self.export_dir / f'{incident_container}.bin'
                Adams.execute_cmd(' '.join([f'file bin write file="{str(file)}"',
                                            f'entity_name={incident_container}',
                                            'alert=no']))
                delete_objects(f'{ans.full_name}.CONTACT_INCIDENTS')
            else:
                file = self.export_dir / f'{ans.name}.res'
                Adams.execute_cmd(' '.join([f'file analysis write file="{str(file)}"',
                                            f'analysis={ans.full_name}']))
                self.files.append(file)
                ans.destroy()

    def rereference(self):
        """Restores all references to `self.entity`

        Parameters
        ----------
        props : dict
            Dictionary of the original dependent properties and their values
        """
        # Loop over Dependent Properties
        for prop in list(self.dep_props):

            # Restore the reference
            if isinstance(prop.value, list):
                setattr(prop.entity, prop.name, [get_object(v, self.mod) for v in prop.value])
            else:
                setattr(prop.entity, prop.name, get_object(prop.value, self.mod))

            self.dep_props.remove(prop)
        
        self.entity_copy.destroy()

        # Load the exported bin files
        for file in self.files:
            if file.suffix == '.bin':
                Adams.execute_cmd(f'file bin read file="{str(file)}" entity_name={file.stem} alert=no')
            
            elif file.suffix == '.res':
                Adams.execute_cmd(f'file analysis read file="{str(file)}" model={self.mod.full_name}')

        if isinstance(self.export_dir, Path) and self.export_dir.exists():
            try:
                rmtree(self.export_dir)
            except Exception:
                pass
