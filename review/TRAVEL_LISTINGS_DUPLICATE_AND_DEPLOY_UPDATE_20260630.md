# Travel Listings Duplicate and Deploy Update

```json
{
  "date": "2026-06-30",
  "chosen_base_deploy": "C:\\Users\\Alyxx and Niko\\Downloads\\NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-06-28_Average_User_Substance_Update.zip",
  "chosen_base_reason": "The uploaded 2026-06-28 deploy had the newer multi-page UI, audio/animation assets, and average-user substance pages. The older workspace canonical zip had more raw rows but fewer developed pages, so the newer deploy was used as the base and the data layer was expanded/deduped into it.",
  "output_site": "C:\\Users\\Alyxx and Niko\\tri_deploy_work_20260630\\travel_updated_v2",
  "output_zip": "C:\\Users\\Alyxx and Niko\\Documents\\Northern New Mexico & Southern Colorado Tri-County Regional Marketing Guide For Businesses, Non-Profits, Entrepreneurs, and Artists\\dist\\NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-06-30_Travel_Listings_Update.zip",
  "downloads_zip": "C:\\Users\\Alyxx and Niko\\Downloads\\NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-06-30_Travel_Listings_Update.zip",
  "travel_listing_pipeline": {
    "raw_input_rows": 523,
    "after_removing_generic_non_listing_rows": 519,
    "after_source_merge_before_strict_accent_pass": 494,
    "final_travel_rows": 493,
    "generic_rows_removed": [
      "About Us",
      "Attractions"
    ],
    "strict_duplicate_merged_after_review": [
      "The Lift Cafe / The Lift Café"
    ],
    "same_name_kept_separate": [
      "Subway in Angel Fire and Subway in Raton are separate locations."
    ]
  },
  "site_counts_after_final_dedupe": {
    "directory_shortcuts": 98,
    "local_inventory_resources": 895,
    "directory_metadata_entries": 993
  },
  "duplicate_checks": {
    "resource_id_duplicate_groups": 0,
    "resource_normalized_name_town_county_duplicate_groups": 0,
    "resource_normalized_name_county_category_duplicate_groups": 0,
    "travel_normalized_name_town_county_duplicate_groups": 0,
    "travel_normalized_name_county_category_duplicate_groups": 0,
    "metadata_entry_id_duplicate_groups": 0,
    "metadata_normalized_name_county_category_kind_duplicate_groups": 0
  },
  "cross_layer_resource_rows_removed_because_shortcut_already_covers_source": [
    "Angel Fire Chamber Member Business Directory",
    "New Mexico Local Economic Development Act",
    "Village of Eagle Nest Business Directory",
    "City of Raton Economic Development Programs",
    "Raton Arts & Cultural District",
    "ROAMS Local Resources",
    "Walsenburg Forms and License Applications",
    "World Journal",
    "Spanish Peaks Community Foundation",
    "Spanish Peaks Country Add Business Listing",
    "Trinidad Community Foundation",
    "Artists Sunday Artist Directory",
    "Colorado Creative Industries",
    "Colexico Alliance / TLAC Chamber Regional Hub"
  ],
  "public_downloads_in_network_page": {
    "travel_excel": "data/Tri_County_Travel_Guide_Listings_20260630.xlsx",
    "travel_csv": "data/tri_county_travel_guide_listings_20260630.csv",
    "visible_links_verified": true
  },
  "publication_note": "Rows are routing leads unless verified by a current public source. Users should confirm details, deadlines, rates, eligibility, contact paths, and publication/placement rules before acting."
}
```
