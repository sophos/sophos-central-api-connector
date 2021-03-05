## Intelix

We have incorporated the SophosLabs Intelix API to assist with cleaning up local site information which can be obtained from the global settings mentioned above.

If you have not used or signed up for the Intelix API further information can be found here: https://api.labs.sophos.com/doc/index.html#registration-howto

We use the Intelix API package as a base: https://github.com/sophos-cybersecurity/intelix

There are a number of options available.

#### Test
You can run a test to ensure that your configuration is working without the need to run the full commands.
```python
python sophos_central_main.py --auth <auth_option> --intelix test
```

#### Report

Running the intelix command in report mode will gather the local site information (all or one tenant) and check Intelix API to see if SophosLabs detect the site.

As part of the process we automatically dedupe the URLs queried with Intelix to reduce the api calls made.

It will automatically generate JSON files for the reports. One which is combined Intelix and local site data: `<date>_<time>_results_combined.json` and another for just the
Intelix results: `<date>_<time>_intelix_results.json`

```python
python sophos_central_main.py --auth <auth_option> --intelix report
```

#### Clean_ls

Running the intelix command with clean_ls will go through the process of checking the sites against the Intelix API and proceed to delete the local-site entry in
the global settings in Sophos Central.

In addition to the clean_ls command you must specify a clean-level to specify which sites that Intelix has a risk level for will be deleted from local-sites. Below are the
accepted risks for the command

- ALL
- HIGH
- HIGH_MEDIUM
- MEDIUM
- LOW

We do not delete sites which have not been categorised by SophosLabs.

Before running the clean_ls command and actively deleting the local sites from Central we highly recommend using the '--dry_run' switch. This will generate a report of what would have
been deleted based on the parameters passed:
```python
python sophos_central_main.py --auth <auth_option> --intelix clean_ls --clean_level <level> --dry_run
```

Please review the dry run report carefully before running the active clean command. The report is: `<tenantId>_<date>_<time>_<clean_level>_dry_run_report.json`

Once you are happy with the dry-run results you can go forward and commit the changes by running the command without the dry-run switch:
```python
python sophos_central_main.py --auth <auth_option> --intelix clean_ls --clean_level <level>
```

Once complete two files will be created. One is a report on the count of deletions etc. for each tenant: `<date>_<time>_deletion_report.json` and another
which is more details on the sites which were sent for deletion, their deletion status and the time of the transaction. This is covered under the file:
`<date>_<time>_deletion_details.json`