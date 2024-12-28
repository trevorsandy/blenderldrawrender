# TODO: remove class
class ImportOptions:
    defaults = {}

    defaults["remove_doubles"] = True
    remove_doubles = defaults["remove_doubles"]

    defaults["recalculate_normals"] = False
    recalculate_normals = defaults["recalculate_normals"]

    defaults["merge_distance"] = 0.05
    merge_distance = defaults["merge_distance"]

    defaults["triangulate"] = False
    triangulate = defaults["triangulate"]

    defaults["meta_bfc"] = True
    meta_bfc = defaults["meta_bfc"]

    defaults["meta_group"] = True
    meta_group = defaults["meta_group"]

    defaults["meta_print_write"] = False
    meta_print_write = defaults["meta_print_write"]

    defaults["meta_step"] = False
    meta_step = defaults["meta_step"]

    defaults["meta_step_groups"] = False
    meta_step_groups = defaults["meta_step_groups"]

    defaults["meta_clear"] = False
    meta_clear = defaults["meta_clear"]

    defaults["meta_pause"] = False
    meta_pause = defaults["meta_pause"]

    defaults["meta_save"] = False
    meta_save = defaults["meta_save"]

    defaults["meta_texmap"] = True
    meta_texmap = defaults["meta_texmap"]

    # _*_lp_lc_mod
    defaults["display_logo"] = True
    # _*_mod_end
    display_logo = defaults["display_logo"]

    # _*_lp_lc_mod
    chosen_logo_choices = (
       #("logo", "Line", "Single line logo geometry"),
       #("logo2", "Outline", "Outlined logo geometry"),
        ("logo3", "Flattened", "Raised flat logo geometry"),
        ("logo4", "Rounded", "Raised rounded logo geometry"),
        ("logo5", "Subtle Rounded", "Subtle rounded logo geometry"),
        ("high-contrast", "High Contrast", "High contrast logo geometry"),
    )
    # _*_mod_end

    defaults["chosen_logo"] = 2
    chosen_logo = defaults["chosen_logo"]

    @staticmethod
    def chosen_logo_value():
        return ImportOptions.chosen_logo_choices[ImportOptions.chosen_logo][0]

    defaults["shade_smooth"] = True
    shade_smooth = defaults["shade_smooth"]

    defaults["make_gaps"] = True
    make_gaps = defaults["make_gaps"]

    defaults["gap_scale"] = 0.997
    gap_scale = defaults["gap_scale"]

    defaults["no_studs"] = False
    no_studs = defaults["no_studs"]

    defaults["set_end_frame"] = True
    set_end_frame = defaults["set_end_frame"]

    defaults["starting_step_frame"] = 1
    starting_step_frame = defaults["starting_step_frame"]

    defaults["frames_per_step"] = 3
    frames_per_step = defaults["frames_per_step"]

    defaults["set_timeline_markers"] = False
    set_timeline_markers = defaults["set_timeline_markers"]

    smooth_type_choices = (
        ("edge_split", "Edge split", "Use an edge split modifier"),
        ("auto_smooth", "Auto smooth", "Use auto smooth"),
        ("bmesh_split", "bmesh smooth", "Split while processing bmesh"),
    )

    defaults["smooth_type"] = 0
    smooth_type = defaults["smooth_type"]

    @staticmethod
    def smooth_type_value():
        return ImportOptions.smooth_type_choices[ImportOptions.smooth_type][0]

    defaults["import_edges"] = False
    import_edges = defaults["import_edges"]

    defaults["bevel_edges"] = False
    bevel_edges = defaults["bevel_edges"]

    defaults["bevel_weight"] = 0.3
    bevel_weight = defaults["bevel_weight"]

    defaults["bevel_width"] = 0.3
    bevel_width = defaults["bevel_width"]

    defaults["bevel_segments"] = 4
    bevel_segments = defaults["bevel_segments"]

    defaults["use_freestyle_edges"] = False
    use_freestyle_edges = defaults["use_freestyle_edges"]

    # _*_lp_lc_mod
    defaults["import_cameras"] = True
    import_cameras = defaults["import_cameras"]

    defaults["import_lights"] = True
    import_lights = defaults["import_lights"]

    defaults["add_environment"] = True
    add_environment = defaults["add_environment"]

    defaults["camera_border_percent"] = True
    camera_border_percent = defaults["camera_border_percent"]
    
    defaults["position_camera"] = True
    position_camera = defaults["position_camera"]
    # _*_mod_end

    defaults["import_scale"] = 0.02
    import_scale = defaults["import_scale"]

    defaults["parent_to_empty"] = False  # True False
    parent_to_empty = defaults["parent_to_empty"]

    defaults["treat_shortcut_as_model"] = False  # TODO: if true parent to empty at median of group
    treat_shortcut_as_model = defaults["treat_shortcut_as_model"]

    scale_strategy_choices = (
        ("mesh", "Scale mesh", "Apply import scaling to mesh. Recommended for rendering"),
        ("object", "Scale object", "Apply import scaling to object. Recommended for part editing"),
    )

    defaults["scale_strategy"] = 1
    defaults["scale_strategy"] = 0
    scale_strategy = defaults["scale_strategy"]

    @staticmethod
    def scale_strategy_value():
        return ImportOptions.scale_strategy_choices[ImportOptions.scale_strategy][0]
