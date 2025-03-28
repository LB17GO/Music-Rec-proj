# Music Recommendation System Project Plan

## Week 1: Planning and Setup

| Member  | Tasks                          | Details                                                                                       |
|---------|--------------------------------|-----------------------------------------------------------------------------------------------|
| Lucy    | Explore dataset, clean data    | - Download the dataset and inspect its structure (e.g., columns, rows, missing values). <br> - Clean the data by handling missing values, removing duplicates, and normalizing features.<br> Perfrom intital feature engineering (e.g., encoding categorical data, scaling numerical data) <br> - Share initial findings with the team. |
| Jakub   | Research collaborative filtering | - Study collaborative filtering algorithms (e.g., SVD, KNN). <br> - Explore libraries like **Surprise** or **Scikit-learn** for implementation. <br> - Share resources and ideas with the team. |
| Waseem  | Research content-based filtering | - Study content-based filtering techniques (e.g., cosine similarity, feature extraction). <br> - Explore how to use song features (e.g., genre, tempo) for recommendations. <br> - Share resources and ideas with the team. |

**Team Meeting**: Discuss the dataset, finalize the approach, and assign tasks for Week 2.

---

## Week 2: Data Preprocessing and EDA

| Member  | Tasks                          | Details                                                                                       |
|---------|--------------------------------|-----------------------------------------------------------------------------------------------|
| Lucy    | Perform EDA, share insights    | - Create visualizations (e.g., histograms, scatterplots, heatmaps) to understand the data. <br> - Analyze trends (e.g., popular genres, user listening habits). <br> - Perform advanced feature engineering (e.g., extracting tempo bins, clustering genres) <br> - Handle class imbalances if necessary <br> - Share insights with the team to guide model development. |
| Jakub   | Review EDA results             | - Analyze the EDA findings to understand user-item interactions. <br> - Plan how to create a user-item interaction matrix for collaborative filtering. |
| Waseem  | Review EDA results             | - Analyze the EDA findings to understand song features. <br> - Plan how to extract and use features for content-based filtering. |

**Team Meeting**: Review EDA results, discuss insights, and plan for model development.

---

## Week 3: Building Basic Models

| Member  | Tasks                          | Details                                                                                       |
|---------|--------------------------------|-----------------------------------------------------------------------------------------------|
| Lucy    | Start researching Front End   | - Research how to combine the algorithm with a website. <br> |
| Jakub   | Build basic CF model    | - Create a user-item interaction matrix (e.g., user-song plays or ratings). <br> - Implement a basic version of a collaborative filtering algorithm (e.g., SVD, KNN). |
| Waseem  | Build basic CB model    | - Extract song features (e.g., genre, tempo, danceability). <br> - Compute similarity between songs (e.g., cosine similarity <br> Start builiding basic CB model |

**Team Meeting**: 
Review basic CF and CB models, ensure both can be combined later, discuss website research


---

## Week 4: Finishing and Evaluating Models

| Member  | Tasks                          | Details                                                                                       |
|---------|--------------------------------|-----------------------------------------------------------------------------------------------|
| Lucy    | Provide feedback on models and start building Front End   | - Start building website <br> - Suggest improvements to models <br> Implement additional feature selection techniques (e.g., PCA or mutual information) to improve song similarity|
| Jakub   | Continue to build and evaluate CF model | - Finish CF model <br> - Evaluate the model using metrics like RMSE or MAE. <br>  - Suggest ways to combine it with content based filtering later. |
| Waseem  | Continue to build and evaluate CB model    |  -Finish CB model <br> - Evaluate the model using metrics like precision, recall, or F1-score. <br> - Suggest ways to combine it with collabrative filtering later |

**Team Meeting**: Review finished CF and CB models, review basic website, plan for the hybrid model.

---

## Week 5: Hybrid Model and Improvements

| Member  | Tasks                          | Details                                                                                       |
|---------|--------------------------------|-----------------------------------------------------------------------------------------------|
| Lucy    | Collaborate on hybrid model    | - Help combine collaborative and content-based filtering (e.g., weighted average). <br> - Suggest feature engineering improvements (e.g., adding lyrics or mood features). |
| Jakub   | Collaborate on hybrid model    | - Help combine collaborative and content-based filtering. <br> - Suggest hyperparameter tuning for better performance. |
| Waseem  | Build and evaluate hybrid model | - Combine collaborative and content-based filtering into a hybrid model. <br> - Evaluate the hybrid model using metrics like MAP or F1-score. <br> - Document the implementation and results. |

**Team Meeting**: Review hybrid model results and finalize improvements.

---

## Week 6: Deployment and Final Touches

| Member  | Tasks                          | Details                                                                                       |
|---------|--------------------------------|-----------------------------------------------------------------------------------------------|
| Lucy    | Contribute to deployment       | - Help save the trained model using `joblib` or `pickle`. <br> - Assist in building a simple web app using **Flask** or **Streamlit**. <br>  Test and optimize data preprocessing pipeline for real-time use.|
| Jakub   | Contribute to deployment       | - Help deploy the model as a web app or API. <br> - Test the deployed system and fix bugs. |
| Waseem  | Contribute to deployment       | - Write the project report or README file. <br> - Prepare a presentation or demo video (optional). |

**Team Meeting**: Finalize the project, review the deployment, and practice the presentation.

---

## Key Collaboration Points

1. **Weekly Sync-Ups**:
   - Discuss progress, challenges, and next steps.
   - Ensure everyone is on the same page.

2. **Code Reviews**:
   - Review each other’s code for quality and consistency.
   - Provide constructive feedback.

3. **Shared Documentation**:
   - Maintain a shared document for project notes, decisions, and resources.
   - Write clear comments in your code for easy understanding.

4. **Task Flexibility**:
   - Be ready to help each other if someone falls behind.
   - Collaborate on key decisions (e.g., model selection, evaluation metrics).

---

By following this plan, your team can work efficiently and collaboratively to build a successful music recommendation system. Good luck, and enjoy the process! 🚀
