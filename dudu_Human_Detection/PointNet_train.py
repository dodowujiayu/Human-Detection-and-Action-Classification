import torch
import torch.nn as nn
import os
from gesture_dataset import GestureDataset
from torch.utils.data import Dataset, DataLoader
# from torchsummary import summary
from tqdm import tqdm
from PointNet import HAR_model

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def test_acc(model, dataset, batch_size):
    dataloader = DataLoader(dataset = dataset,batch_size=batch_size,shuffle=False)
    model.eval()

    test_correct = 0
    for data in tqdm(dataloader,ascii=True):
        inputs, states, targets = data[0].to(device), data[1].to(device), data[2].to(device)
        # print(data[0].size(),data[1].size())
        outputs = model(inputs)

        _, pred = torch.max(outputs, 1)
        test_correct += torch.sum(pred == targets)
        # print(test_correct)
    del dataloader
    print("Test Accuracy {:.4f}%".format(100.0*test_correct/len(dataset)))



if __name__ == '__main__':
    batch_size = 70
    test_batch = 100
    learning_rate = 0.01

    seed = 2021
    epoch_num = 200

    dataset_test = GestureDataset(train=False, with_state=True)

    dataset = GestureDataset(train=True, with_state=True)
    train_loader = DataLoader(dataset = dataset,batch_size=batch_size,shuffle=True)

    model = HAR_model(output_dim = 4, frame_num = 20,hidden_size=16)
    # summary(model,(1,60,250,11))
    model.to(device)

    if os.path.exists('./models/gesture_PointNet.pkl'):
        model.load_state_dict(torch.load('./models/gesture_PointNet.pkl',map_location = device))
        print("load model sucessfully")

    adam = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(adam, step_size=2, gamma=0.8)

    crossloss = nn.CrossEntropyLoss()
    for epoch in range(1, epoch_num+1):
        test_acc(model,dataset_test,test_batch)
        model.train()
        epoch_loss = 0

        for batch, data in enumerate(tqdm(train_loader,ascii = True)):
            inputs, states, targets = data[0].to(device), data[1].to(device), data[2].to(device)
            outputs = model(inputs)
            loss = crossloss(outputs,targets)

            adam.zero_grad()
            loss.backward()
            adam.step()
            epoch_loss += loss

            # print('epoch:{}\t batch:{}/{}\t batch loss:{:.4f}'.format(epoch,batch,len(train_loader),loss))
        scheduler.step()
        print('epoch:{}\t epoch loss:{:.4f} \t learning rate:{}'.format(epoch, epoch_loss, adam.param_groups[0]['lr']))
        torch.save(model.state_dict(), "./models/gesture_PointNet.pkl")

