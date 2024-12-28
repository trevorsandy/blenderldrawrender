class ExportOptions:
    defaults = {}

    defaults["remove_doubles"] = False
    remove_doubles = defaults["remove_doubles"]

    defaults["merge_distance"] = 0.05
    merge_distance = defaults["merge_distance"]

    defaults["recalculate_normals"] = False
    recalculate_normals = defaults["recalculate_normals"]

    defaults["triangulate"] = False
    triangulate = defaults["triangulate"]

    defaults["ngon_handling"] = "triangulate"
    ngon_handling = defaults["ngon_handling"]

    # _*_lp_lc_mod
    # moved to export_type_choices
    #defaults["selection_only"] = True
    #selection_only = defaults["selection_only"]
    # _*_mod_end

    defaults["export_precision"] = 2
    export_precision = defaults["export_precision"]

    # _*_lp_lc_mod
    export_type_choices = (
        ("model_parts_only", "Model Parts", "Export top model collection parts" ),
        ("selection_only", "Selection", "Export selected items"),
    )

    defaults['export_type'] = 0
    export_type = defaults['export_type']

    @staticmethod
    def export_type_value():
        return ExportOptions.export_type_choices[ExportOptions.export_type][0]
    # _*_mod_end