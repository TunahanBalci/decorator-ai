# Firestore Seed Data

`design_projects.json` mirrors the app's curated mock data in Firestore shape.

Firestore collections:

- `designProjects/{projectId}`
- `designProjects/{projectId}/products/{productId}`
- `scans/{scanId}`

Import the seed data with the Firebase CLI or copy the documents manually in the Firebase Console. Deploy rules and indexes with:

```sh
firebase deploy --only firestore
```
