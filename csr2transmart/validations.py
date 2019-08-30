class BlueprintValidations:
    def __init__(self, modifier_dimensions=set()):
        self.dimensions = {'patient'} | modifier_dimensions

    def collect_tree_node_dimension_violations(self, blueprint):
        for column, declarations in blueprint.items():
            if 'label' in declarations and declarations['label'] in ['MODIFIER', 'OMIT', 'SUBJ_ID']:
                continue
            if self._no_dimension_field(declarations):
                yield f"{column}: No subject dimension metadata tag specified."
            elif self._get_dimension(declarations) not in self.dimensions:
                yield f"{column}: \"{self._get_dimension(declarations)}\" subject dimension is not recognised."

    def _no_dimension_field(self, column_declarations):
        return 'metadata_tags' not in column_declarations or\
               'subject_dimension' not in column_declarations['metadata_tags']

    def _get_dimension(self, column_declarations):
        return column_declarations['metadata_tags']['subject_dimension']


def get_blueprint_validator_initialised_with_modifiers(modifiers_table_file):
    import pandas
    mod_df = pandas.read_csv(modifiers_table_file, sep='\t')
    modifier_dimension_names = set(mod_df['name_char'])
    return BlueprintValidations(modifier_dimension_names)
