import sys
import src.offline.create_metadata as metadata
import src.offline.upload_offline as upload

# TODO move stuff from upload_offline here, leave the real code there

if sys.argv[1] == '--create_metadata':
    outpath = 'config/fieldmappings.json'
    metadata.print_all(outpath)

elif sys.argv[1] == '--create_mode':
    mode = sys.argv[2]
    suffix = sys.argv[3]
    upload.create_mode(mode, suffix)
    print('Upload successful')

elif sys.argv[1] == '--create_empty_index':
    mode = sys.argv[2]
    suffix = sys.argv[3]
    upload.create_empty_index(mode, suffix)
    print('Index created successfully')

elif sys.argv[1] == '--import_mode':
    mode = sys.argv[2]
    suffix = sys.argv[3]
    upload.create_mode(mode, suffix, with_id=True)
    print('Upload successful')

elif sys.argv[1] == '--publish_mode':
    group = sys.argv[2]
    suffix = sys.argv[3]
    upload.publish_group(group, suffix)
    print('Upload successful')

elif sys.argv[1] == '--reindex_alias':
    print('reindex')
    index = sys.argv[2]
    target_suffix = sys.argv[3]
    upload.reindex_alias(index, target_suffix)

elif sys.argv[1] == '--getmapping':
    import src.offline.getmapping as gm
    alias = sys.argv[2]
    outfile = sys.argv[3]
    gm.getmapping(alias, outfile)

elif sys.argv[1] == '--internalize_lexicon':
        # adds a lexicon to sql from es
        # can be done at any time, not noticable
        # to the end user
        mode = sys.argv[2]
        to_upload = sys.argv[3:]
        upload.internalize_lexicon(mode, to_upload)
        print('Upload successful')

elif sys.argv[1] == '--printlatestversion':
    lexicon = sys.argv[2]
    upload.printlatestversion(lexicon)

elif sys.argv[1] == '--exportlatestversion':
    lexicon = sys.argv[2]
    upload.printlatestversion(lexicon, debug=False, with_id=True)

# Commented since dangerous!
# if sys.argv[1] == '--delete_all':
#    upload.delete_all()
#    print('Deletion successful')
#
#
# # Commented since dangerous!
# if sys.argv[1] == '--delete_mode':
#    mode = sys.argv[2]
#    upload.delete_mode(mode)
#    print('Deletion successful')

else:
     print("Don't know what to do")
