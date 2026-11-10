# Methodology and limitations

OSS Evidence Kit produces candidate-evidence reports from GitHub's public REST Search API. Its goal is reproducibility and reviewability, not automated eligibility decisions.

## Community-builder route

The tool searches for merged pull requests in a repository using a query equivalent to:

```text
repo:OWNER/REPO is:pr is:merged merged:>=YYYY-MM-DD
```

It then:

1. Excludes PRs authored by the repository owner's login.
2. Excludes bot usernames recognized by the tool (`[bot]`, `-bot`, `dependabot`, and `renovate`).
3. Counts distinct remaining GitHub logins, not pull requests.
4. Includes PR URLs for manual review.

**Why the output says “candidate external contributors”:** the public search result does not prove that an author is external to the project. A person may be a collaborator, maintainer, employee, or organization member. The tool deliberately does not label these accounts as verified external contributors.

## Active-contributor route

The tool searches for merged pull requests authored by a GitHub login within the selected date window. It excludes repositories whose owner login exactly matches the supplied personal username and includes the remaining PRs as candidate contributions.

This is a conservative but incomplete approximation. A user may own an organization account or be a maintainer of an organization-owned project. Those relationships are not inferred. Review each repository and remove any project that the applicant owns or controls.

## Date window

The default is 365 days ending on the local system date at the time the report is generated. The report records an inclusive `merged:>=YYYY-MM-DD` query start and the report-generation date. The API's indexed search results may lag recent GitHub activity.

## GitHub Search limitations

GitHub Search limits a query to at most 1,000 results. The report includes `search_truncated_or_incomplete`; do not rely on the candidate threshold when that value is `true`. Search may also return incomplete results. A `GITHUB_TOKEN` or `GH_TOKEN` can improve rate limits, but does not remove all API limitations.

## What this tool does not verify

- Whether an account is a true outside contributor rather than a collaborator or maintainer.
- Whether the applicant owns or controls an organization-owned repository.
- Private contributions that are not visible to the token.
- Whether merged PRs are substantive, non-automated, or accepted as qualifying by a program reviewer.
- Package downloads, dependent package/repository counts, foundation membership, or OpenSSF Criticality Score.
- Whether an applicant meets a program's residency, account-age, license, or other non-project terms.

## Recommended review before submitting a report

1. Open every listed PR and check that it was merged within the stated period.
2. Remove bots, maintainers, collaborators, organizational insiders, and any other accounts that do not meet the program's definition of an external contributor.
3. For active-contributor reports, remove any repository the applicant owns or controls, including organization-owned repositories.
4. Check the program's official application page and terms on the date of application.
5. Keep the generated report and the official GitHub links as supporting documentation; do not present the CLI output as an official certification.
