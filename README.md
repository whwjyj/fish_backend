# 딥러닝을 이용한 모둠회 재료 인식 앱 개발

# 기술 스택
✓Frontend

![React Native](https://img.shields.io/badge/React%20Native-4FC08D?style=for-the-badge&logo=React&logoColor=white)


✓ Backend

[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

✓ DB Server

[![AWS EC2](https://img.shields.io/badge/AWS%20EC2-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/ec2/)

✓ API Test & Tools

<img src="https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white">

✓ Infra & DevOps

<img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github"> ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white)
![Figma](https://img.shields.io/badge/Figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white)

# 프로젝트 소개

1) **기획의도**
    - 본 프로젝트는 딥러닝 기술을 활용하여 모둠회 이미지를 인식하고, 구성된 회의 종류를 사용자에게 실시간으로 알려주는 애플리케이션을 개발하는 것을 목표로 한다.
2) **프로젝트 내용**
    - 사용자가 스마트폰 카메라를 이용해 모둠회 사진을 찍으면, 딥러닝 모델인 YOLOv8을 사용하여 사진 속의 회 종류를 실시간으로 인식하고 분류한다. 이후 인식된 결과를 사용자에게 시각적으로 제공하며, 지속적인 학습을 통해 모델의 정확도를 향상시킨다.
3) **정의**
    - 모둠회 재료 인식 앱은 사용자가 모둠회 사진을 촬영하면, 해당 이미지에서 각 회의 종류를 식별하여 알려주는 딥러닝 기반 애플리케이션이다.

### 개발 배경 및 필요성

1) **프로젝트 제작 동기**
    - 회는 다양한 종류가 있으며, 일반 소비자가 이를 구분하는 것이 쉽지 않다. 특히, 회를 처음 접하는 사람들에게는 회의 종류를 식별하는 것이 큰 어려움이 될 수 있다. 이러한 문제를 해결하고자 딥러닝 기술을 활용하여 모둠회 이미지를 인식하고,
      각 회의 종류를 사용자에게 알려주는 애플리케이션을 개발하게 되었다.
2) **프로젝트 제작 목적**
    - 사용자가 모둠회를 쉽게 식별할 수 있도록 돕고, 회식 문화에서 더 나은 선택을 할 수 있도록 지원한다. 이를 통해 음식에 대한 이해도를 높이고, 사용자 경험을 개선한다.

### 프로젝트 특·장점

1) **주요 기능**
    - 모둠회 사진 촬영, 실시간 회 종류 인식, 회 정보 검색, 제철 회 정보 제공, 사용자 문의 기능 등 다양한 기능을 제공한다.
2) **신규 창작 프로젝트로서의 독창성**
    - (기존) 이미지 인식 애플리케이션으로 기존 제품은 명함 인식, 한자 필기 인식, 서류 인식 등의 제품이 있으나 모둠회 재료 인식 프로젝트처럼 음식을 인식하는 기능을 가진 유사한 제품은 없다.
    - (특장점) 따라서 본 프로젝트는 다음과 같은 독창성이 있다. YOLOv8 모델을 활용하여 다양한 회 종류를 정확하게 인식함으로써 높은 정확도와 신뢰성을 제공하는 점과 사용자로부터 수집된 데이터를 바탕으로 모델을 지속적으로 학습시켜, 시간이 지날수록 더        정확한 모둠회 재료 인식 결과를 제공한다는 점, React Native를 사용하여 iOS와 Android에서 모두 사용할 수 있는 앱을 개발하여 사용자 기반을 넓히고 다양한 디바이스에서 일관된 사용자 경험을 제공하는 점이다.

### 기대효과 및 활용분야

1. **프로젝트의 기대효과** 
    - 기존 서비스와의 차별성 : 본 프로젝트는 기존의 회 인식 서비스가 없다는 점이 독창적이고 기존의 이미지 인식 서비스와 비교했을 때에는, 최신 딥러닝 기술인 YOLOv8을 활용하여 높은 정확도로 회 종류를 실시간으로 인식한다는 차별성이 있다.
      이를 통해 사용자는 더 빠르고 정확한 정보를 얻을 수 있으며, 음식 선택의 폭을 넓힐 수 있다.
    - 시장성 : 모둠회 인식 앱은 요식업계, 특히 회 전문점과 같은 분야에서 큰 시장성을 가질 수 있다. 정확한 회 인식 기술을 통해 고객 만족도를 높이고, 회 선택 과정에서의 불편함을 줄일 수 있기 때문이다.
      
 2. **프로젝트의 활용분야**
    - 요식업계 : 회 전문점이나 일식 레스토랑에서 손님들에게 제공되는 회 종류를 정확히 안내할 수 있다. 이를 통해 고객 만족도를 높이고, 신뢰를 구축할 수 있다.
    - 교육 분야 : 회에 대한 정보를 제공하여 학습 자료로 활용할 수 있다. 특히, 요리 학교나 요리 강좌에서 회 종류를 학습하는 데 유용하게 사용될 수 있다.
    - 개인 사용자 : 회를 자주 접하지 않는 일반 소비자들에게 회 종류를 쉽게 인식하고 선택할 수 있도록 도와준다. 이를 통해 회를 처음 접하는 사람들도 다양한 회를 경험할 수 있게 된다.
    - 여행 및 관람 : 외국인 관광객들에게 한국의 다양한 회 종류를 소개하고, 선택할 수 있도록 도와준다. 이를 통해 한국 음식 문화에 대한 이해를 높일 수 있다.
   
# 기획

<details>
  <summary>WBS</summary>
    <img width="630" height="491" alt="스크린샷 2025-10-01 오전 11 32 46" src="https://github.com/user-attachments/assets/cbf85ca8-df60-4cdc-852e-c1a24f8de74b" />
</details>

<details>
  <summary>유즈케이스</summary>
    <img width="616" height="362" alt="스크린샷 2025-10-01 오전 11 36 44" src="https://github.com/user-attachments/assets/07e2b802-a16f-4873-b0ee-0b5145d665a1" />
</details>

<details>
  <summary>서비스 흐름도</summary>
    <img width="364" height="329" alt="스크린샷 2025-10-01 오전 11 37 23" src="https://github.com/user-attachments/assets/cd66185a-1324-460f-9907-570b5cfaafb5" />
</details>

<details>
  <summary>기능 흐름도</summary>
<img width="633" height="343" alt="스크린샷 2025-10-01 오전 11 38 11" src="https://github.com/user-attachments/assets/2b503990-fc46-4561-a1a9-e08b1ebe7897" />
</details>

# 시스템 아키텍처 및 기술적 특징
<img width="478" height="351" alt="스크린샷 2025-10-01 오전 11 35 30" src="https://github.com/user-attachments/assets/59ef58b5-0cff-4524-96f5-c1118ab4561c" />


   
